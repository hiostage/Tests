from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="Заголовок поста")
    content = Column(Text, nullable=False, comment="Содержание поста")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="Дата создания")
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment="Дата обновления")
    
    # Внешние ключи
    author_id = Column(Integer, ForeignKey("users_cache.id"), index=True, comment="ID автора")
    group_id = Column(Integer, ForeignKey("groups.id"), index=True, comment="ID группы")
    
    # Дополнительные поля
    is_pinned = Column(Boolean, default=False, comment="Закреплен ли пост")
    status = Column(String(20), default='published', index=True, comment="Статус поста")  # черновик, опубликован, архив
    tags = Column(JSON, default=[], comment="Теги поста") 
    views_count = Column(Integer, default=0, comment="Количество просмотров")
    last_activity_at = Column(DateTime, onupdate=datetime.utcnow, comment="Последняя активность")
    edited_by = Column(Integer, ForeignKey("users_cache.id"), nullable=True, comment="Кто редактировал")
    edit_reason = Column(String(200), nullable=True, comment="Причина редактирования")

    # Связи с другими моделями
    author = relationship(
    "User", 
    back_populates="posts", 
    foreign_keys=[author_id], 
    lazy="selectin"
    )

    editor = relationship(
        "User", 
        back_populates="edited_posts", 
        foreign_keys=[edited_by], 
        lazy="selectin"
    )

    group = relationship("Group", back_populates="posts", lazy="selectin")
    
    # Для модерации
    
    

    async def increment_views(self, db: AsyncSession):
        """Увеличивает счетчик просмотров (асинхронно)"""
        stmt = update(Post).where(Post.id == self.id).values(
            views_count=self.views_count + 1, 
            last_activity_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()

    async def update_from_data(self, db: AsyncSession, data: dict):
        """Обновляет пост из словаря данных (асинхронно)"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'author_id']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        await db.commit()

    async def is_editable_by(self, db: AsyncSession, user_id: int) -> bool:
        """Проверяет, может ли пользователь редактировать пост (асинхронно)"""
        result = await db.execute(
            select(Post.author_id).where(Post.id == self.id)
        )
        author_id = result.scalar_one_or_none()
        return author_id == user_id
