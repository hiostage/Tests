from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate, GroupWithMembers
from fastapi import HTTPException, status
from typing import List, Optional
from app.utils.logger import logger
from app.services.user import UserService
from app.utils.cache import cache
from datetime import datetime
from functools import wraps

def handle_db_errors(func):
    """Декоратор для обработки ошибок БД"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error"
            )
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )
    return wrapper

class GroupService:
    @staticmethod
    @cache.cached(ttl=300, key_prefix="group")
    @handle_db_errors
    def get_group(db: Session, group_id: int) -> Optional[GroupWithMembers]:
        """Получение группы с информацией о членах"""
        group = db.query(Group).options(
            joinedload(Group.members),
            joinedload(Group.creator)
        ).filter(Group.id == group_id).first()
        
        if group:
            return GroupWithMembers.from_orm(group)
        return None

    @staticmethod
    @cache.cached(ttl=60, key_prefix="groups_list")
    @handle_db_errors
    def get_groups(db: Session, skip: int = 0, limit: int = 100) -> List[GroupWithMembers]:
        """Получение списка групп с пагинацией"""
        groups = db.query(Group).options(
            joinedload(Group.creator)
        ).offset(skip).limit(limit).all()
        return [GroupWithMembers.from_orm(group) for group in groups]

    @staticmethod
    @handle_db_errors
    async def create_group(db: Session, group_data: GroupCreate, creator_id: int) -> GroupWithMembers:
        """Создание новой группы с проверкой создателя"""
        # Проверяем существование создателя
        creator = await UserService.get_user_from_auth_service(creator_id)
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Creator not found"
            )
        
        logger.info(
            f"Creating group: {group_data.name[:50]}, "
            f"creator: {creator_id}"
        )
        
        try:
            db_group = Group(
                **group_data.dict(),
                creator_id=creator_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(db_group)
            db.commit()
            db.refresh(db_group)
            
            logger.info(f"Group created: {db_group.id}")
            
            # Инвалидируем кеш списка групп
            await cache.delete("groups_list")
            
            return GroupWithMembers.from_orm(db_group)
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Group creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group with this name already exists"
            )

    @staticmethod
    @handle_db_errors
    async def update_group(
        db: Session, 
        group_id: int, 
        group_data: GroupUpdate
    ) -> GroupWithMembers:
        """Обновление информации о группе"""
        db_group = db.query(Group).filter(Group.id == group_id).first()
        if not db_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        update_data = group_data.dict(exclude_unset=True)
        for field in update_data:
            setattr(db_group, field, update_data[field])
        
        db_group.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_group)
        
        # Инвалидируем кеш
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")
        
        return GroupWithMembers.from_orm(db_group)

    @staticmethod
    @handle_db_errors
    async def delete_group(db: Session, group_id: int) -> GroupWithMembers:
        """Удаление группы"""
        db_group = db.query(Group).filter(Group.id == group_id).first()
        if not db_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        db.delete(db_group)
        db.commit()
        
        # Инвалидируем кеш
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")
        
        return GroupWithMembers.from_orm(db_group)

    @staticmethod
    @handle_db_errors
    async def add_member(
        db: Session, 
        group_id: int, 
        user_id: int
    ) -> GroupWithMembers:
        """Добавление участника в группу"""
        db_group = db.query(Group).options(
            joinedload(Group.members)
        ).filter(Group.id == group_id).first()
        
        if not db_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Проверяем существование пользователя
        user = await UserService.get_user_from_auth_service(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        if any(member.id == user_id for member in db_group.members):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already in group"
            )
        
        db_group.members.append(user)
        db_group.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_group)
        
        # Инвалидируем кеш
        await cache.delete(f"group:{group_id}")
        
        return GroupWithMembers.from_orm(db_group)

    @staticmethod
    @handle_db_errors
    async def remove_member(
        db: Session, 
        group_id: int, 
        user_id: int
    ) -> GroupWithMembers:
        """Удаление участника из группы"""
        db_group = db.query(Group).options(
            joinedload(Group.members)
        ).filter(Group.id == group_id).first()
        
        if not db_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        if not any(member.id == user_id for member in db_group.members):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not in group"
            )
        
        db_group.members = [
            member for member in db_group.members 
            if member.id != user_id
        ]
        db_group.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_group)
        
        # Инвалидируем кеш
        await cache.delete(f"group:{group_id}")
        
        return GroupWithMembers.from_orm(db_group)