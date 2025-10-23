from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.models.group import Group, group_members
from app.schemas.group import GroupCreate, GroupUpdate, GroupWithMembers, GroupList
from fastapi import HTTPException, status, Request, Depends
from typing import List, Optional
from app.schemas.user import UserPublic
from app.utils.logger import logger
from app.services.user import UserService
from app.utils.cache import cache
from datetime import datetime
from functools import wraps
from app.models import User


def handle_db_errors(func):
    """Декоратор для обработки ошибок БД"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Вызов оригинальной функции
            return await func(*args, **kwargs)
        except IntegrityError as e:
            logger.error(f"Integrity error while accessing group: {str(e)}")
            raise HTTPException(status_code=400, detail="Integrity error")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper

class GroupService:
    @staticmethod
    async def add_member_to_group(db: AsyncSession, group_id: int, user_id: int, role: str = "member"):
        """Добавляет пользователя в группу, если он ещё не является её участником"""
        
        # Проверяем, есть ли уже такой пользователь в группе
        stmt = select(group_members).filter(group_members.c.group_id == group_id, group_members.c.user_id == user_id)
        result = await db.execute(stmt)
        existing_member = result.first()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже является участником группы"
            )
        
        # Вставляем нового члена в группу
        new_member = group_members.insert().values(
            group_id=group_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow(),
            is_banned=False
        )
        
        await db.execute(new_member)
        
        # Обновляем количество участников в группе
        group = await db.get(Group, group_id)
        group.member_count += 1
        await db.commit()
        await db.refresh(group)

        # Загружаем связанные данные
        await db.refresh(group, ["creator", "members"])
        
        # Создаём и возвращаем GroupWithMembers
        return GroupWithMembers.from_orm(
            group,
            user_id=user_id,
            is_member=True
        )
        
    @staticmethod
    @handle_db_errors
    async def get_group(db: AsyncSession, group_id: int, user_id: int):
        # Получаем группу по id
        stmt = select(Group).filter(Group.id == group_id)
        result = await db.execute(stmt)
        db_group = result.scalars().first()

        if not db_group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Логика проверки, является ли пользователь участником группы
        # Можно добавить свою проверку, например, через отдельный метод, или напрямую через запрос
        is_member = await GroupService.is_member(db, db_group.id, user_id)

        # Преобразуем группу в GroupWithMembers, добавляя информацию о текущем пользователе
        return GroupWithMembers.from_orm(db_group, user_id=user_id, is_member=is_member)

    @staticmethod
    @handle_db_errors
    async def is_member(db: AsyncSession, group_id: int, user_id: int) -> bool:
        """Проверяет, является ли пользователь участником группы (асинхронно)"""
        result = await db.execute(
            select(group_members).where(
                group_members.c.group_id == group_id, group_members.c.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    @handle_db_errors
    async def get_groups(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user_id: int = Depends(UserService.get_user_id_from_session),
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        """Получение списка групп с пагинацией и total"""
        logger.debug("Building query for groups")

        stmt = select(Group).options(selectinload(Group.creator))
        
        if category:
            logger.debug(f"Filtering by category: {category}")
            stmt = stmt.where(Group.category == category)

        if search:
            logger.debug(f"Filtering by search term: {search}")
            stmt = stmt.where(
                Group.name.ilike(f"%{search}%") | Group.description.ilike(f"%{search}%")
            )

        try:
            # Получаем общее количество для пагинации
            count_stmt = stmt.with_only_columns(func.count()).order_by(None)
            total_result = await db.execute(count_stmt)
            total = total_result.scalar_one()

            logger.debug(f"Total count of groups: {total}")

            # Применяем offset и limit
            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            groups = result.scalars().all()

            logger.debug(f"Retrieved {len(groups)} groups from the database")

            # Преобразуем в нужные схемы
            serialized_groups = [GroupWithMembers.from_orm(group, user_id=user_id) for group in groups]

            return {
                "groups": serialized_groups,
                "total": total,
                "limit": limit,
                "offset": skip
            }

        except Exception as e:
            logger.error(f"Error while fetching groups: {str(e)}")
            raise e
    
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
        
        logger.debug(f"Creating group with data: {group_data}")

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
        
        logger.debug(f"Deleting group with id: {group_id}")

        await db.delete(db_group)
        await db.commit()
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")
        
        # Передаем user_id в GroupWithMembers.from_orm
        return GroupWithMembers.from_orm(db_group, user_id=user_id)
    
    @staticmethod
    @handle_db_errors
    async def remove_member(db: AsyncSession, group_id: int, user_id: int) -> dict:
        """Удаляет участника из группы"""
        
        # Проверяем, существует ли группа
        group_stmt = select(Group).filter(Group.id == group_id)
        group_result = await db.execute(group_stmt)
        db_group = group_result.scalars().first()
        if not db_group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Проверяем, существует ли пользователь
        user_stmt = select(User).filter(User.id == user_id)
        user_result = await db.execute(user_stmt)
        db_user = user_result.scalars().first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Проверяем, является ли пользователь участником группы
        member_stmt = select(group_members).filter(
            group_members.c.group_id == group_id,
            group_members.c.user_id == user_id
        )
        result = await db.execute(member_stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a member of this group")
        
        # Удаляем участника из группы
        delete_member_stmt = group_members.delete().where(
            group_members.c.group_id == group_id,
            group_members.c.user_id == user_id
        )
        await db.execute(delete_member_stmt)

        # Обновляем количество участников в группе
        db_group.member_count -= 1
        db.add(db_group)  # Добавляем измененную группу в сессию
        await db.commit()

        # Получаем обновленную информацию о группе и участниках
        members_stmt = select(User).join(group_members).filter(group_members.c.group_id == group_id)
        members_result = await db.execute(members_stmt)
        members = members_result.scalars().all()

        # Создаем объект GroupWithMembers
        return GroupWithMembers.from_orm(
            db_group,
            user_id=user_id,
            members=[UserPublic.from_orm(member) for member in members],
            is_member=False  # Указываем, что пользователь больше не является участником группы
        )
    

