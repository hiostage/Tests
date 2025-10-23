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

from app.exceptions.errors import *

from app.exceptions.error_handlers import handler_decorator

class GroupService():
    def __init__(self, db: AsyncSession):
        self.db = db
        
    @handler_decorator
    async def add_member_to_group(self, group_id: int, user_id: str, role: str = "member"):
        """Добавляет пользователя в группу, если он ещё не является её участником"""
        
        logger.debug(f"Attempting to add user {user_id} to group {group_id} with role {role}")
        
        # Проверяем, есть ли уже такой пользователь в группе
        
        stmt = select(User).join(group_members).filter(group_members.c.group_id == group_id, group_members.c.user_id == user_id)
        result = await self.db.execute(stmt)

        if result.scalars().first():
            logger.warning(f"User {user_id} is already a member of group {group_id}")
            self.handle_error(UserAlreadyMember)
        
        # Вставляем нового члена в группу
        new_member = group_members.insert().values(
            group_id=group_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow(),
            is_banned=False
        )
        
        await self.db.execute(new_member)
        
        # Обновляем количество участников в группе
        group = await self.db.get(Group, group_id)
        group.member_count += 1
        await self.db.commit()
        await self.db.refresh(group)

        # Загружаем связанные данные
        await self.db.refresh(group, ["creator", "members"])
        
        # Создаём и возвращаем GroupWithMembers
        logger.debug(f"User {user_id} successfully added to group {group_id}")
        return GroupWithMembers.from_group(
            group,
            user_id=user_id,
            is_member=True
        )

        
    @handler_decorator
    async def get_group(self, group_id: int, user_id: str):
        logger.debug(f"Fetching group {group_id} with user {user_id}")
        
        # Получаем группу по id
        db_group = await self.get_group_by_id(group_id)
        
        # Логика проверки, является ли пользователь участником группы
        is_member = await self.is_member(db_group.id, user_id)

        # Преобразуем группу в GroupWithMembers, добавляя информацию о текущем пользователе
        return GroupWithMembers.from_group(db_group, user_id=user_id, is_member=is_member)



    @handler_decorator
    async def get_groups(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: str = Depends(UserService.get_user_id_from_session),
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

        # Получаем общее количество для пагинации
        count_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        logger.debug(f"Total count of groups: {total}")

        # Применяем offset и limit
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        groups = result.scalars().all()

        logger.debug(f"Retrieved {len(groups)} groups from the database")

        # Преобразуем в нужные схемы
        serialized_groups = [GroupWithMembers.from_group(group, user_id=user_id) for group in groups]

        return {
            "groups": serialized_groups,
            "total": total,
            "limit": limit,
            "offset": skip
        }

    @handler_decorator
    async def create_group(self, group_data: GroupCreate, creator_id: int, request: Request) -> GroupWithMembers:
        """Создание новой группы"""
        creator = await UserService.get_current_user_from_session(request)
        if not creator:
            self.handle_error(CreatorNotFound, f"Creator not found for group creation. creator_id: {creator_id}")
        
        # Проверка, существует ли уже группа с таким названием
        existing_group = await self.db.execute(
            select(Group).filter(Group.name == group_data.name)
        )
        if existing_group.scalars().first():
            self.handle_error(GroupNameAlreadyExists, f"Group with name {group_data.name} already exists")
        
        logger.debug(f"Creating group with data: {group_data}")

        # Создаем группу
        db_group = Group(
            **group_data.dict(),
            creator_id=creator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(db_group)
        await self.db.commit()
        await self.db.refresh(db_group)

        # Добавляем создателя в группу
        await db_group.add_member(self.db, creator)

        logger.info(f"Group {db_group.name} created successfully with ID: {db_group.id}")

        await cache.delete("groups_list")

        return GroupWithMembers.from_group(db_group, user_id=creator_id)

    @handler_decorator
    async def update_group(self, group_id: int, group_data: GroupUpdate, user_id: str) -> GroupWithMembers:
        """Обновление информации о группе"""
        stmt = select(Group).filter(Group.id == group_id)
        result = await self.db.execute(stmt)
        db_group = result.scalars().first()

        if not db_group:
            self.handle_error(GroupNotFound, f"Group with ID {group_id} not found for update")
        
        for field, value in group_data.dict(exclude_unset=True).items():
            setattr(db_group, field, value)
        db_group.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(db_group)
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")

        logger.info(f"Group {db_group.id} updated successfully")

        # Передаем user_id в GroupWithMembers.from_group
        return GroupWithMembers.from_group(db_group, user_id=user_id)

    @handler_decorator
    async def delete_group(self, group_id: int, user_id: str) -> GroupWithMembers:
        """Удаление группы"""
        stmt = select(Group).filter(Group.id == group_id)
        result = await self.db.execute(stmt)
        db_group = result.scalars().first()

        if not db_group:
            self.handle_error(GroupNotFound, f"Group with ID {group_id} not found for deletion")
        
        logger.debug(f"Deleting group with id: {group_id}")

        await self.db.delete(db_group)
        await self.db.commit()
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")

        logger.info(f"Group {group_id} deleted successfully")

        # Передаем user_id в GroupWithMembers.from_group
        return GroupWithMembers.from_group(db_group, user_id=user_id)

    @handler_decorator
    async def remove_member(self, group_id: int, user_id: str) -> dict:
        """Удаляет участника из группы"""
        
        # Проверяем, существует ли группа
        db_group = db_group = await self.get_group_by_id(group_id)
        
        # Проверяем, существует ли пользователь
        user_stmt = select(User).filter(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        db_user = user_result.scalars().first()
        if not db_user:
            self.handle_error(UserNotFound, f"User with ID {user_id} not found for removal from group {group_id}")

        # Проверяем, является ли пользователь участником группы
        stmt = select(User).join(group_members).filter(group_members.c.group_id == group_id, group_members.c.user_id == user_id)
        result = await self.db.execute(stmt)

        if not result.scalars().first():
            logger.warning(f"User {user_id} not member this group {group_id}")
            self.handle_error(UserNotMemberThisGroup)
        
        # Удаляем участника из группы
        delete_member_stmt = group_members.delete().where(
            group_members.c.group_id == group_id,
            group_members.c.user_id == user_id
        )
        await self.db.execute(delete_member_stmt)

        # Обновляем количество участников в группе
        db_group.member_count -= 1
        self.db.add(db_group)  # Добавляем измененную группу в сессию
        await self.db.commit()

        logger.debug(f"Updated member count for group {group_id}: {db_group.member_count}")

        # Получаем обновленную информацию о группе и участниках
        members_stmt = select(User).join(group_members).filter(group_members.c.group_id == group_id)
        members_result = await self.db.execute(members_stmt)
        members = members_result.scalars().all()

        logger.info(f"User {user_id} removed from group {group_id}")

        # Создаем объект GroupWithMembers
        return GroupWithMembers.from_group(
            db_group,
            user_id=user_id,
            members=[UserPublic.from_orm(member) for member in members],
            is_member=False  # Указываем, что пользователь больше не является участником группы
        )
    
    @handler_decorator
    async def is_member(self, group_id: int, user_id: str) -> bool:
        """Проверяет, является ли пользователь участником группы (асинхронно)"""
        logger.debug(f"Checking membership for user {user_id} in group {group_id}")
        
        result = await self.db.execute(
            select(group_members).where(
                group_members.c.group_id == group_id, group_members.c.user_id == user_id
            )
        )
        is_member = result.scalar_one_or_none() is not None
        
        if not is_member:
            logger.debug(f"User {user_id} is {'a member' if is_member else 'not a member'} of group {group_id}")
            self.handle_error(UserNotMemberThisGroup)
        
        return is_member
    
    async def get_group_by_id(self, group_id):
        stmt = select(Group).filter(Group.id == group_id)
        result = await self.db.execute(stmt)
        group = result.scalars().first()

        if not group:
            self.handle_error(GroupNotFound, f"Group with id {group_id} not found")
        
        return group

    def handle_error(self, exception_cls: type[Exception], log_message: str | None = None):
        if log_message:
            logger.error(log_message)
        raise exception_cls()

    async def update_member_count(self):
        """Обновляет счетчик участников (асинхронный вариант)"""
        result = await self.db.execute(
            select(func.count()).select_from(group_members).where(group_members.c.group_id == self.id)
        )
        self.member_count = result.scalar_one()
        return self.member_count

    async def add_member(self, user):
        """Добавляет участника в группу (асинхронно)"""
        if not await self.is_member(user.id):
            await self.db.execute(group_members.insert().values(
                group_id=self.id,
                user_id=user.id,
                joined_at=datetime.utcnow()
            ))
            await self.update_member_count(self.db)
            await self.db.commit()
            return True
        return False

    async def remove_member_pattern(self, user):
        """Удаляет участника из группы (асинхронно)"""
        if await self.is_member(self.db, user.id):
            await self.db.execute(group_members.delete().where(
                group_members.c.group_id == self.id, group_members.c.user_id == user.id
            ))
            await self.db.commit()
            await self.update_member_count(self.db)
            return True
        return False


