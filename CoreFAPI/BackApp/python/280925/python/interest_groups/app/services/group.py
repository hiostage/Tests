from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from app.models.group import Group, group_members
from app.schemas.group import GroupCreate, GroupUpdate, GroupWithMembers
from fastapi import Request
from typing import Optional
from app.schemas.user import UserPublic
from app.utils.logger import logger
from app.utils.cache import cache
from datetime import datetime
from app.models import User
from app.exceptions.errors import UserAlreadyMember, GroupNotFound, GroupNameAlreadyExists, CreatorOnly, UserNotMemberThisGroup
from app.exceptions.error_handlers import handler_decorator
from app.utils.rabbitmq import RabbitMQManager

UserNotMember = "User not a member"

class GroupService():
    def __init__(self, db: AsyncSession, current_user):
        self.db = db
        self.current_user = current_user
        
    @handler_decorator
    async def add_member_to_group(self, group_id: int, user_id: str, role: str = "member"):
        """Добавляет пользователя в группу, если он ещё не является её участником"""

        logger.debug(f"Attempting to add user {user_id} to group {group_id} with role {role}")

        await self.is_creator(group_id, self.current_user.id)

        await self.add_member(user_id, group_id, role)
        
        group = await self.db.get(Group, group_id)
        # Загружаем связанные данные
        await self.db.refresh(group, ["creator", "members"])
        
        # Создаём и возвращаем GroupWithMembers
        logger.debug(f"User {user_id} successfully added to group {group_id}")

        await RabbitMQManager.publish_event(
            event_type="user_added_to_group",
            payload={
                "group_id": group_id,
                "uuid": user_id
            },
            routing_key="event.new_member"
        )

        return GroupWithMembers.from_group(
            group,
            user_id=user_id,
            is_member=True
        )

    @handler_decorator
    async def get_group(self, group_id: int):
        logger.debug(f"Fetching group {group_id} with user {self.current_user.id}")
        
        # Получаем группу по id
        db_group = await self.get_group_by_id(group_id)

        # Логика проверки, является ли пользователь участником группы
        is_member = await self.is_member(db_group.id, self.current_user.id)

        if not is_member:
            await self.handle_error(UserNotMemberThisGroup, UserNotMember)

        # Преобразуем группу в GroupWithMembers, добавляя информацию о текущем пользователе
        return GroupWithMembers.from_group(db_group, user_id=self.current_user.id, is_member=is_member)

    @handler_decorator
    async def get_groups(
        self,
        skip: int = 0,
        limit: int = 100,
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
        serialized_groups = [GroupWithMembers.from_group(group, user_id=self.current_user.id) for group in groups]

        return {
            "groups": serialized_groups,
            "total": total,
            "limit": limit,
            "offset": skip
        }

    @handler_decorator
    async def create_group(self, group_data: GroupCreate, request: Request) -> GroupWithMembers:
        """Создание новой группы"""
        # Проверка, существует ли уже группа с таким названием
        existing_group = await self.db.execute(
            select(Group).filter(Group.name == group_data.name)
        )
        if existing_group.scalars().first():
            await self.handle_error(GroupNameAlreadyExists, f"Group with name {group_data.name} already exists")
        
        logger.debug(f"Creating group with data: {group_data}")

        # Создаем группу
        db_group = Group(
            **group_data.dict(),
            creator_id=self.current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(db_group)
        await self.db.commit()
        await self.db.refresh(db_group)

        # Добавляем создателя в группу
        await self.add_member(user_id=self.current_user.id, group_id=db_group.id, role="admin")

        logger.info(f"Group {db_group.name} created successfully with ID: {db_group.id}")

        await RabbitMQManager.publish_event(
            event_type="group_created",
            payload={
                "group_id": db_group.id,
                "group_name": db_group.name,
                "creator_id": self.current_user.id
            },
            routing_key="event.new_group"
        )

        await cache.delete("groups_list")

        return GroupWithMembers.from_group(db_group, user_id=self.current_user.id)

    @handler_decorator
    async def update_group(self, group_id: int, group_data: GroupUpdate) -> GroupWithMembers:
        """Обновление информации о группе"""
    
        db_group = await self.is_creator(group_id, self.current_user.id)

        for field, value in group_data.dict(exclude_unset=True).items():
            setattr(db_group, field, value)
        db_group.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(db_group)
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")

        logger.info(f"Group {db_group.id} updated successfully")

        # Передаем user_id в GroupWithMembers.from_group
        return GroupWithMembers.from_group(db_group, user_id=self.current_user.id)

    @handler_decorator
    async def delete_group(self, group_id: int) -> GroupWithMembers:
        """Удаление группы"""

        db_group = await self.is_creator(group_id, self.current_user.id)
        
        logger.debug(f"Deleting group with id: {group_id}")

        await self.db.delete(db_group)
        await self.db.commit()
        await cache.delete(f"group:{group_id}")
        await cache.delete("groups_list")

        logger.info(f"Group {group_id} deleted successfully")

        # Передаем user_id в GroupWithMembers.from_group
        return GroupWithMembers.from_group(db_group, user_id=self.current_user.id)

    @handler_decorator
    async def remove_member(self, group_id: int, user_id: str) -> dict:
        """Удаляет участника из группы"""
        
        # Проверяем, существует ли группа
        db_group = await self.is_creator(group_id, self.current_user.id)
    
        await self.remove_member_pattern(user_id, group_id, db_group)

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

    ####PATTERNS####
    async def is_creator(self, group_id: int, user_id: str):
        db_group = await self.get_group(group_id)

        if user_id != db_group.creator_id:
            logger.warning("Только создатель может выполнить данное действие")
            await self.handle_error(CreatorOnly)
        
        return db_group

    async def is_member(self, group_id: int, user_id: str) -> bool:
        """Проверяет, является ли пользователь участником группы (асинхронно)"""
        logger.debug(f"Checking membership for user {user_id} in group {group_id}")
        result = await self.db.execute(
            select(group_members).where(
                group_members.c.group_id == group_id, group_members.c.user_id == user_id
            )
        )
        is_member = result.scalar_one_or_none() is not None
        return is_member

    async def handle_error(self, exception_cls: type[Exception], log_message: str | None = None, cache_ttl: int = 5):
        cache_key = f"error:{self.current_user.id}:{exception_cls.__name__}" 
        await cache.set(cache_key, {"type": exception_cls.__name__, "message": log_message}, ttl=cache_ttl)

        keys_list = await cache.get(f"error_keys:{self.current_user.id}") or []

        if cache_key not in keys_list:
            keys_list.append(cache_key)
            await cache.set(f"error_keys:{self.current_user.id}", keys_list, ttl=cache_ttl)

        if log_message:
            logger.error(log_message)
        raise exception_cls()

    async def get_group_by_id(self, group_id):
        stmt = select(Group).filter(Group.id == group_id)
        result = await self.db.execute(stmt)
        group = result.scalars().first()
        if not group:
            await self.handle_error(GroupNotFound, f"Group with id {group_id} not found")
            
        return group
    
    async def update_member_count(self, group_id):
        """Обновляет счетчик участников (асинхронный вариант)"""
        db_group = await self.get_group_by_id(group_id)
        result = await self.db.execute(
            select(func.count()).select_from(group_members).where(group_members.c.group_id == group_id)
        )
        db_group.member_count = result.scalar_one()
        logger.debug(f"Updated member count for group {group_id}: {db_group.member_count}")
        return db_group.member_count

    async def add_member(self, user_id: str, group_id: int, role: str):
        """Добавляет участника в группу (асинхронно)"""
        if not await self.is_member(group_id, user_id):
            await self.db.execute(group_members.insert().values(
                group_id=group_id,
                user_id=user_id,
                role=role,
                joined_at=datetime.utcnow()
            ))
            await self.update_member_count(group_id)
            await self.db.commit()
            return True
        await self.handle_error(UserAlreadyMember, "User already member")
        return False

    async def remove_member_pattern(self, user_id, group_id, db_group):
        """Удаляет участника из группы (асинхронно)"""
        if not db_group:
            logger.debug(f"Group with id {group_id} not found")
            await self.handle_error(GroupNotFound)
        if await self.is_member(group_id, user_id):
            await self.db.execute(group_members.delete().where(
                group_members.c.group_id == group_id, group_members.c.user_id == user_id
            ))
            await self.update_member_count(group_id)
            await self.db.commit()
            return True
        await self.handle_error(UserNotMemberThisGroup, UserNotMember)
        return False
    ####PATTERNS####


