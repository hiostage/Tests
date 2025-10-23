from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users_cache"  # Уточняем, что это кеш
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True)  
    email = Column(String(100), index=True)   
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, default=datetime.utcnow)
    
    # Опциональные кешированные отношения
    groups = relationship(
        "Group", 
        secondary="group_members", 
        back_populates="members",
        lazy="selectin"  # Для оптимизации запросов
    )
    
    # Методы для работы с кешем
    def needs_refresh(self, ttl_minutes=60):
        return (datetime.utcnow() - self.last_sync_at).total_seconds() > ttl_minutes * 60

    def update_from_external(self, external_data: dict):
        """Обновление данных из внешнего сервиса"""
        self.username = external_data.get('username', self.username)
        self.email = external_data.get('email', self.email)
        self.is_active = external_data.get('is_active', True)
        self.last_sync_at = datetime.utcnow()

    