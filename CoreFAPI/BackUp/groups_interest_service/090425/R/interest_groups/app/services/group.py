from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from app.models.group import Group, group_members
from app.schemas.group import GroupCreate, GroupUpdate, GroupWithMembers
from fastapi import HTTPException, status, Request, Depends
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
    async def add_member_to_group(db: AsyncSession, group_id: int, user_id: int, role: str = "member"):
        """Добавляет пользователя в группу, если он еще не является её участником"""
        
        # Проверяем, есть ли уже такой пользователь в группе
        stmt = select(group_members).filter_by(group_id=group_id, user_id=user_id)
        result = await db.execute(stmt)
        existing_member = result.first()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже является участником группы"
            )
        
        # Вставляем нового члена в группу, если такого еще нет
        new_member = group_members.insert().values(
            group_id=group_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow(),
            is_banned=False  # можно добавить дополнительные поля
        )
        
        await db.execute(new_member)
        await db.commit()


    @staticmethod
    @cache.cached(ttl=300, key_prefix="group")
    @handle_db_errors
    async def get_group(db: AsyncSession, group_id: int, user_id: int) -> Optional[GroupWithMembers]:
        """Получение группы с информацией о членах"""
        stmt = (
            select(Group)
            .options(selectinload(Group.members), selectinload(Group.creator))
            .filter(Group.id == group_id)
        )
        result = await db.execute(stmt)
        group = result.scalars().first()
        return GroupWithMembers.from_orm(group, user_id=user_id) if group else None

    @staticmethod
    @cache.cached(ttl=60, key_prefix="groups_list")
    @handle_db_errors
    async def get_groups(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        user_id: int = Depends(UserService.get_user_id_from_session)  # Добавляем зависимость
    ) -> List[GroupWithMembers]:
        """Получение списка групп с пагинацией"""
        stmt = select(Group).options(selectinload(Group.creator)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        groups = result.scalars().all()
        return [GroupWithMembers.from_orm(group, user_id=user_id) for group in groups]

    @staticmethod
    @handle_db_errors
    async def create_group(db: AsyncSession, group_data: GroupCreate, creator_id: int, request: Request) -> GroupWithMembers:
        """Создание новой группы"""
        creator = await UserService.get_current_user_from_session(request)
        if not creator:
            raise HTTPException(status_code=400, detail="Creator not found")
        
        # Проверка, существует ли уже группа с таким названием
        existing_group = await db.execute(
            select(Group).filter(Group.name == group_data.name)
        )
        if existing_group.scalars().first():
            raise HTTPException(status_code=400, detail="A group with this name already exists")

        # Создаем группу
        db_group = Group(
            **group_data.dict(),
            creator_id=creator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(db_group)
        await db.commit()
        await db.refresh(db_group)

        # Добавляем создателя в группу
        await db_group.add_member(db, creator)

        await cache.delete("groups_list")
        return GroupWithMembers.from_orm(db_group, user_id=creator_id)


    @staticmethod
    @handle_db_errors
    async def update_group(db: AsyncSession, group_id: int, group_data: GroupUpdate, user_id: int) -> GroupWithMembers:
        """Обновление информации о группе"""
        stmt = select(Group).filter(Group.id == group_id)
        result = await db.execute(stmt)
        db_group = result.scalars().first()
        if not db_group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        for field, value in group_data.dict(exclude_unset=True).items():
            setattr(db_group, field, value)
        db_group.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(db_group)
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")
        
        # Передаем user_id в GroupWithMembers.from_orm
        return GroupWithMembers.from_orm(db_group, user_id=user_id)

    @staticmethod
    @handle_db_errors
    async def delete_group(db: AsyncSession, group_id: int, user_id: int) -> GroupWithMembers:
        """Удаление группы"""
        stmt = select(Group).filter(Group.id == group_id)
        result = await db.execute(stmt)
        db_group = result.scalars().first()
        if not db_group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        await db.delete(db_group)
        await db.commit()
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")
        
        # Передаем user_id в GroupWithMembers.from_orm
        return GroupWithMembers.from_orm(db_group, user_id=user_id)
    

