from sqlalchemy.orm import Session
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate
from fastapi import HTTPException, status
from typing import List

def get_group(db: Session, group_id: int):
    return db.query(Group).filter(Group.id == group_id).first()

def get_groups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Group).offset(skip).limit(limit).all()

def create_group(db: Session, group: GroupCreate, creator_id: int):
    db_group = Group(**group.dict(), creator_id=creator_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def update_group(db: Session, group_id: int, group: GroupUpdate):
    db_group = get_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    update_data = group.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_group, field, update_data[field])
    
    db.commit()
    db.refresh(db_group)
    return db_group

def delete_group(db: Session, group_id: int):
    db_group = get_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.delete(db_group)
    db.commit()
    return db_group

def add_member_to_group(db: Session, group_id: int, user_id: int):
    db_group = get_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id in [member.id for member in db_group.members]:
        raise HTTPException(status_code=400, detail="User already in group")
    
    db_group.members.append(user_id)
    db.commit()
    db.refresh(db_group)
    return db_group

def remove_member_from_group(db: Session, group_id: int, user_id: int):
    db_group = get_group(db, group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id not in [member.id for member in db_group.members]:
        raise HTTPException(status_code=400, detail="User not in group")
    
    db_group.members = [member for member in db_group.members if member.id != user_id]
    db.commit()
    db.refresh(db_group)
    return db_group