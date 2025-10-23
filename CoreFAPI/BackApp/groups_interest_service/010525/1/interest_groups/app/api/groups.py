from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from datetime import timedelta
from app.schemas.group import Group, GroupCreate, GroupUpdate, GroupWithMembers, GroupList
from app.services.group import GroupService
from app.db.session import get_db
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache
from fastapi import Request, Depends
from sqlalchemy.exc import IntegrityError
from app.services.user import UserService

from app.utils.rabbitmq import RabbitMQManager

router = APIRouter(tags=["groups"])
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=Group,
    status_code=status.HTTP_201_CREATED
)
async def create_new_group(
    request: Request,
    group: GroupCreate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    """Create a new group"""
    if not user_data.get("is_active"):
        raise HTTPException(status_code=403, detail="Inactive user cannot create groups")
    
    if "groups.write" not in user_data.get("permissions", []):
        raise HTTPException(status_code=403, detail="Missing required permission")
    
    try:
        # Получаем создателя группы с помощью новой функции
        creator = await UserService.get_user_by_id(db, user_data["user_id"])
        
        if not creator:
            raise HTTPException(status_code=404, detail="Creator not found")
        
        # Создаём группу
        group = await GroupService.create_group(
            db=db,
            group_data=group,
            creator_id=user_data["user_id"],
            request=request
        )

        # Формируем объект GroupWithMembers с добавленными участниками и создателем
        group_with_members = GroupWithMembers.from_group(group, user_id=user_data["user_id"], creator=creator, members=[])

        await RabbitMQManager.publish_event(
            event_type="group_created",
            payload={
                "group_id": group.id,
                "group_name": group.name,
                "creator_id": user_data["user_id"]
            },
            routing_key="event.new_group"
        )

        return group_with_members
    
    except IntegrityError:
        logger.error("IntegrityError occurred while creating the group")
        raise HTTPException(status_code=400, detail="Group name exists")
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not create group")




@router.get("/check_auth", include_in_schema=False)
async def check_auth(user_data: dict = Depends(get_current_user)):
    """Эндпоинт для проверки аутентификации"""
    return {"status": "authenticated", "user_id": user_data["user_id"]}

@router.get(
    "/",
    response_model=GroupList,
    description="Get list of groups with pagination"
)
@cache(expire=30)
async def read_groups(
    skip: int = 0,
    limit: int = Query(default=100, le=500, description="Max 500 items"),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(UserService.get_user_id_from_session)
):
    """Получаем список групп с пагинацией"""
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    logger.info(f"Fetching groups with skip={skip}, limit={limit}, category={category}, search={search}")

    try:
        data = await GroupService.get_groups(db, skip=skip, limit=limit, category=category, search=search, user_id=user_id)
        logger.info(f"Successfully fetched {len(data['groups'])} groups out of {data['total']} total groups")
        return GroupList(**data)
    except Exception as e:
        logger.error(f"Error fetching groups: {str(e)}")
        raise e
    
@router.get(
    "/{group_id}",
    response_model=GroupWithMembers,
    responses={404: {"description": "Group not found"}}
)
@cache(expire=60)
async def read_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(UserService.get_user_id_from_session),
):
    """Get group details with members list"""
    db_group = await GroupService.get_group(db, group_id=group_id, user_id=user_id)
    if not db_group:
        raise HTTPException(status_code=404, detail=f"Group with id {group_id} not found")
    return db_group

@router.put(
    "/{group_id}",
    response_model=Group,
    responses={403: {"description": "Not authorized"}, 404: {"description": "Group not found"}}
)
async def update_existing_group(
    group_id: int,
    group: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    """Update group information"""
    db_group = await GroupService.get_group(db, group_id=group_id, user_id=user_data["user_id"])
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if db_group.creator_id != user_data["user_id"]:
        raise HTTPException(status_code=403, detail="Only group creator can update group")
    
    try:
        return await GroupService.update_group(
            db=db,
            group_id=group_id,
            group_data=group,
            user_id=user_data["user_id"]
        )
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not update group")

@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"description": "Not authorized"}, 404: {"description": "Group not found"}}
)
async def delete_existing_group(
    group_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    """Delete a group"""
    db_group = await GroupService.get_group(db, group_id=group_id, user_id=user_data["user_id"])
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if db_group.creator_id != user_data["user_id"]:
        raise HTTPException(status_code=403, detail="Only group creator can delete group")
    
    try:
        await GroupService.delete_group(db=db, group_id=group_id, user_id=user_data["user_id"])
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not delete group")

@router.post(
    "/{group_id}/members/{user_id}",
    response_model=GroupWithMembers,
    responses={
        403: {"description": "Not authorized"},
        404: {"description": "Group or user not found"},
        409: {"description": "User already in group"}
    }
)
async def add_member(
    group_id: int,
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    # Синхронизируем текущего пользователя (создателя)
    await UserService.sync_user(db, user_data)

    # Синхронизируем того, кого хотим добавить
    mocked_user_data = {
        "user_id": user_id,
        "username": f"user_{user_id}",
        "email": f"user_{user_id}@mock.local",
        "is_active": True,
    }
    await UserService.sync_user(db, mocked_user_data)

    db_group = await GroupService.get_group(db, group_id=group_id, user_id=user_data["user_id"])
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if db_group.creator_id != user_data["user_id"]:
        raise HTTPException(status_code=403, detail="Only group creator can add members")
    
    try:
        # Добавляем участника в группу
        group_with_members = await GroupService.add_member_to_group(
            db=db,
            group_id=group_id,
            user_id=user_id
        )

        # Публикуем событие о добавлении нового участника в группу
        await RabbitMQManager.publish_event(
            event_type="user_added_to_group",
            payload={
                "group_id": group_id,
                "user_id": user_id
            },
            routing_key="event.new_member"
        )

        return group_with_members
    except IntegrityError:
        raise HTTPException(status_code=409, detail="User is already a member")
    except Exception as e:
        logger.error(f"Error adding member {user_id} to group {group_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not add user to group")

@router.delete(
    "/{group_id}/members/{user_id}",
    response_model=GroupWithMembers,
    responses={403: {"description": "Not authorized"}, 404: {"description": "Group or user not found"}}
)
async def remove_member(
    group_id: int,
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    """Remove user from group"""
    db_group = await GroupService.get_group(db, group_id=group_id, user_id=user_data["user_id"])
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if db_group.creator_id != user_data["user_id"] and user_data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only creator or user themselves can remove")
    
    try:
        return await GroupService.remove_member(
            db=db,
            group_id=group_id,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error removing member {user_id} from group {group_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not remove user from group")