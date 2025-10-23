from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from app.schemas.group import Group, GroupCreate, GroupUpdate, GroupWithMembers, GroupList
from app.services.group import GroupService
from app.db.session import get_db
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache
from fastapi import Request, Depends
from app.services.user import UserService
from app.schemas.user import UserFull

router = APIRouter(tags=["groups"])
logger = logging.getLogger("app")

@router.post("/", response_model=Group, status_code=status.HTTP_201_CREATED)
async def create_new_group(
    request: Request,
    group: GroupCreate,
    db: AsyncSession = Depends(get_db),
    user_data: UserFull = Depends(get_current_user)
):
    """Create a new group"""
    user = await UserService.sync_user(db, user_data)
    logger.info(f"User synchronized: {user}")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user cannot create groups")

    # if "groups.write" not in user_data.get("permissions", []):
    #     raise HTTPException(status_code=403, detail="Missing required permission")

    # Создаём группу
    group_services = GroupService(db, user_data)
    group = await group_services.create_group(group_data=group, request=request)

    # Формируем объект GroupWithMembers с добавленными участниками и создателем
    group_with_members = GroupWithMembers.from_group(group, user_id=user_data.id, creator=user_data, members=[])

    return group_with_members

@router.get("/check_auth", include_in_schema=False)
async def check_auth(user_data: UserFull = Depends(get_current_user)):
    """Эндпоинт для проверки аутентификации"""
    return {"status": "authenticated", "user_id": user_data.id}

@router.get("/", response_model=GroupList, description="Get list of groups with pagination")
@cache(expire=30)
async def read_groups(
    skip: int = 0,
    limit: int = Query(default=100, le=500, description="Max 500 items"),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_data: UserFull = Depends(get_current_user)
):
    """Получаем список групп с пагинацией"""
    
    logger.info(f"Fetching groups with skip={skip}, limit={limit}, category={category}, search={search}")
    group_services = GroupService(db, user_data)

    data = await group_services.get_groups(skip=skip, limit=limit, category=category, search=search)
    logger.info(f"Successfully fetched {len(data['groups'])} groups out of {data['total']} total groups")
    return GroupList(**data)
    
@router.get("/{group_id}", response_model=GroupWithMembers)
@cache(expire=60)
async def read_group(group_id: int, db: AsyncSession = Depends(get_db), user_data: UserFull = Depends(get_current_user)):
    """Get group details with members list"""
    group_services = GroupService(db, user_data)
    db_group = await group_services.get_group(group_id=group_id)
    return db_group

@router.put("/{group_id}", response_model=Group)
async def update_existing_group(
    group_id: int,
    group: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    user_data: UserFull = Depends(get_current_user)
):
    """Update group information"""
    group_services = GroupService(db, user_data)
    return await group_services.update_group(group_id=group_id, group_data=group)
 

@router.delete("/{group_id}")
async def delete_existing_group(
    group_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: UserFull = Depends(get_current_user)
):
    """Delete a group"""
    group_services = GroupService(db, user_data)
    await group_services.delete_group(group_id=group_id)

@router.post("/{group_id}/members/{user_id}", response_model=GroupWithMembers)
async def add_member(
    group_id: int,
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: UserFull = Depends(get_current_user)
):
    # Синхронизируем текущего пользователя (создателя)
    await UserService.sync_user(db, user_data)

    # Синхронизируем того, кого хотим добавить
    mocked_user_data = {
        "uuid": user_id,
        "firstName": f"User",
        "lastName": f"{user_id}",
        "userName": f"user_{user_id}",
        "email": f"user_{user_id}@mock.local",
        "is_active": True
    }

    await UserService.sync_user(db, UserFull(**mocked_user_data))
    
    # Добавляем участника в группу
    group_services = GroupService(db, user_data)
    return await group_services.add_member_to_group(group_id=group_id, user_id=user_id)

@router.delete("/{group_id}/members/{user_id}", response_model=GroupWithMembers)
async def remove_member(
    group_id: int,
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_data: UserFull = Depends(get_current_user)
):
    """Remove user from group"""

    group_services = GroupService(db, user_data)
    return await group_services.remove_member(group_id, user_id)