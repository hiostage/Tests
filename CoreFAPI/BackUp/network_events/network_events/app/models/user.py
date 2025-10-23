from sqlalchemy import Column, Integer, String, DateTime, Boolean, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime, timedelta


class User(Base):
    __tablename__ = "users_cache"  # Уточняем, что это кеш
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True)  
    email = Column(String(100), index=True)   
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, default=lambda: datetime.utcnow())
    # Связь с постами
    posts = relationship(
    "Post", 
    back_populates="author", 
    foreign_keys="[Post.author_id]",
    lazy="selectin"
    )

    edited_posts = relationship(
        "Post",
        back_populates="editor",
        foreign_keys="[Post.edited_by]",
        lazy="selectin"
    )
    # Опциональные кешированные отношения
    groups = relationship(
        "Group", 
        secondary="group_members", 
        back_populates="members",
        lazy="selectin"
    )

    created_groups = relationship(
        "Group", 
        back_populates="creator", 
        lazy="selectin"
    )

    created_groups = relationship("Group", back_populates="creator", lazy="selectin")
    
    async def is_stale(self, ttl_minutes=60) -> bool:
        """Проверяет, устарели ли данные пользователя"""
        return (datetime.utcnow() - self.last_sync_at) > timedelta(minutes=ttl_minutes)

    async def update_from_external(self, db: AsyncSession, external_data: dict):
        """Обновление данных из внешнего сервиса (асинхронно)"""
        stmt = (
            update(User)
            .where(User.id == self.id)
            .values(
                username=external_data.get("username", self.username),
                email=external_data.get("email", self.email),
                is_active=external_data.get("is_active", self.is_active),
                last_sync_at=datetime.utcnow()
            )
        )
        await db.execute(stmt)
        await db.commit()
