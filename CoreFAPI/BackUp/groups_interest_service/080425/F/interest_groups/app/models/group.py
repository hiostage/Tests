from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Table, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

# Ассоциативная таблица для связи групп и пользователей
group_members = Table(
    'group_members',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True, comment="ID группы"),
    Column('user_id', Integer, ForeignKey('users_cache.id'), primary_key=True, comment="ID пользователя"),
    Column('joined_at', DateTime, default=datetime.utcnow, comment="Дата вступления"),
    Column('role', String(50), default='member', comment="Роль в группе"),  # member, moderator, admin
    Column('is_banned', Boolean, default=False, comment="Забанен ли пользователь")
)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор")
    name = Column(String(100), unique=True, index=True, nullable=False, comment="Название группы")
    slug = Column(String(120), unique=True, index=True, comment="ЧПУ для URL")
    description = Column(Text, comment="Описание группы")
    category = Column(String(50), index=True, comment="Категория группы")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="Дата создания")
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment="Дата обновления")
    creator_id = Column(Integer, ForeignKey("users_cache.id"), index=True, comment="ID создателя")
    is_public = Column(Boolean, default=True, comment="Публичная ли группа")
    banner_url = Column(String(255), comment="URL баннера группы")
    rules = Column(Text, comment="Правила группы")
    tags = Column(JSON, default=[], comment="Теги группы")
    member_count = Column(Integer, default=0, comment="Количество участников")

    # Связи с другими моделями
    posts = relationship("Post", back_populates="group", lazy="selectin")
    members = relationship("User", secondary=group_members, back_populates="groups", lazy="selectin")
    creator = relationship("User", back_populates="created_groups", lazy="joined")

    async def update_member_count(self, db: AsyncSession):
        """Обновляет счетчик участников (асинхронный вариант)"""
        result = await db.execute(
            select(func.count()).select_from(group_members).where(group_members.c.group_id == self.id)
        )
        self.member_count = result.scalar_one()
        return self.member_count

    async def is_member(self, db: AsyncSession, user_id: int) -> bool:
        """Проверяет, является ли пользователь участником группы (асинхронно)"""
        result = await db.execute(
            select(group_members).where(
                group_members.c.group_id == self.id, group_members.c.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_member(self, db: AsyncSession, user):
        """Добавляет участника в группу (асинхронно)"""
        if not await self.is_member(db, user.id):
            await db.execute(group_members.insert().values(
                group_id=self.id,
                user_id=user.id,
                joined_at=datetime.utcnow()
            ))
            await db.commit()
            await self.update_member_count(db)
            return True
        return False

    async def remove_member(self, db: AsyncSession, user):
        """Удаляет участника из группы (асинхронно)"""
        if await self.is_member(db, user.id):
            await db.execute(group_members.delete().where(
                group_members.c.group_id == self.id, group_members.c.user_id == user.id
            ))
            await db.commit()
            await self.update_member_count(db)
            return True
        return False
