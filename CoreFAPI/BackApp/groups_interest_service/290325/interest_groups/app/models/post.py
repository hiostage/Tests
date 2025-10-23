from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
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
    
    # Связи с другими моделями
    author = relationship(
        "User", 
        back_populates="posts",
        lazy="selectin"  # Жадная загрузка по умолчанию
    )
    
    group = relationship(
        "Group", 
        back_populates="posts",
        lazy="selectin"
    )
    
    # Для модерации
    edited_by = Column(Integer, ForeignKey("users_cache.id"), nullable=True, comment="Кто редактировал")
    edit_reason = Column(String(200), nullable=True, comment="Причина редактирования")

    def increment_views(self):
        """Увеличивает счетчик просмотров"""
        self.views_count = (self.views_count or 0) + 1
        self.last_activity_at = datetime.utcnow()

    def update_from_data(self, data: dict):
        """Обновляет пост из словаря данных"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'author_id']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def is_editable_by(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь редактировать пост"""
        return self.author_id == user_id