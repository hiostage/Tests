from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.group import Group, GroupCreate, GroupUpdate, GroupWithMembers
from app.services.group import (
    get_group, get_groups, create_group, 
    update_group, delete_group, add_member_to_group, 
    remove_member_from_group
)
from app.db.session import get_db
from app.utils.auth import get_current_user
from app.schemas.user import User

router = APIRouter()

@router.post("/", response_model=Group, status_code=status.HTTP_201_CREATED)
def create_new_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_group(db=db, group=group, creator_id=current_user.id)
    # return create_group(db=db, group=group, creator_id=1)

@router.get("/", response_model=List[Group])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = get_groups(db, skip=skip, limit=limit)
    return groups

@router.get("/{group_id}", response_model=GroupWithMembers)
def read_group(group_id: int, db: Session = Depends(get_db)):
    db_group = get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

@router.put("/{group_id}", response_model=Group)
def update_existing_group(
    group_id: int,
    group: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_group = get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can update the group")
    return update_group(db=db, group_id=group_id, group=group)

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_group = get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete the group")
    delete_group(db=db, group_id=group_id)
    return {"ok": True}

@router.post("/{group_id}/members/{user_id}", response_model=GroupWithMembers)
def add_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_group = get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can add members")
    return add_member_to_group(db=db, group_id=group_id, user_id=user_id)

@router.delete("/{group_id}/members/{user_id}", response_model=GroupWithMembers)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_group = get_group(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.creator_id != current_user.id and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only creator or user themselves can remove")
    return remove_member_from_group(db=db, group_id=group_id, user_id=user_id)