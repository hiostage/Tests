from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.schemas.group import Group, GroupCreate, GroupUpdate, GroupWithMembers
from app.services.group import (
    get_group, get_groups, create_group, 
    update_group, delete_group, add_member_to_group, 
    remove_member_from_group, is_group_member
)
from app.db.session import get_db
from app.utils.auth import get_current_user
from app.schemas.user import User
from fastapi_cache.decorator import cache

router = APIRouter(tags=["groups"])
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=Group,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Group created successfully"},
        400: {"description": "Invalid input data"},
        403: {"description": "Not authorized"}
    }
)
def create_new_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new group
    
    - **name**: required, unique
    - **description**: optional
    - **category**: required (technology, science, etc.)
    - **is_public**: optional (default: true)
    """
    try:
        return create_group(db=db, group=group, creator_id=current_user.id)
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Could not create group. Name might be taken."
        )

@router.get(
    "/",
    response_model=List[Group],
    description="Get list of groups with pagination"
)
@cache(expire=30)
def read_groups(
    skip: int = 0,
    limit: int = Query(default=100, le=500, description="Max 500 items"),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated list of groups
    
    - Supports filtering by category
    - Supports basic search by name
    """
    return get_groups(db, skip=skip, limit=limit, category=category, search=search)

@router.get(
    "/{group_id}",
    response_model=GroupWithMembers,
    responses={404: {"description": "Group not found"}}
)
@cache(expire=60)
def read_group(group_id: int, db: Session = Depends(get_db)):
    """Get group details with members list"""
    db_group = get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {group_id} not found"
        )
    return db_group

@router.put(
    "/{group_id}",
    response_model=Group,
    responses={
        403: {"description": "Not group creator"},
        404: {"description": "Group not found"}
    }
)
def update_existing_group(
    group_id: int,
    group: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update group information
    
    Only group creator can update
    """
    db_group = get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only group creator can update group"
        )
    try:
        return update_group(db=db, group_id=group_id, group=group)
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not update group")

@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Not group creator"},
        404: {"description": "Group not found"}
    }
)
def delete_existing_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a group
    
    Also removes all group posts and memberships
    """
    db_group = get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only group creator can delete group"
        )
    try:
        delete_group(db=db, group_id=group_id)
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Could not delete group"
        )

@router.post(
    "/{group_id}/members/{user_id}",
    response_model=GroupWithMembers,
    responses={
        403: {"description": "Not group creator"},
        404: {"description": "Group or user not found"},
        409: {"description": "User already in group"}
    }
)
def add_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add user to group members
    
    Requires:
    - Current user is group creator
    - User exists in the system
    - User not already in group
    """
    db_group = get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only group creator can add members"
        )
    if is_group_member(db, group_id, user_id):
        raise HTTPException(
            status_code=409,
            detail="User is already in the group"
        )
    try:
        return add_member_to_group(db=db, group_id=group_id, user_id=user_id)
    except Exception as e:
        logger.error(f"Error adding member {user_id} to group {group_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Could not add user to group"
        )

@router.delete(
    "/{group_id}/members/{user_id}",
    response_model=GroupWithMembers,
    responses={
        403: {"description": "Not authorized"},
        404: {"description": "Group or user not found"}
    }
)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove user from group
    
    Allowed for:
    - Group creator
    - User themselves (leaving group)
    """
    db_group = get_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only creator or user themselves can remove"
        )
    try:
        return remove_member_from_group(db=db, group_id=group_id, user_id=user_id)
    except Exception as e:
        logger.error(f"Error removing member {user_id} from group {group_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Could not remove user from group"
        )