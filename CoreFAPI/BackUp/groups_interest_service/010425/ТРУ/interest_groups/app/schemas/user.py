from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Минимальная схема пользователя только для чтения"""
    id: int
    username: str
    email: Optional[str]
    is_active: bool = True

class UserPublic(UserBase):
    """Публичная схема для отдачи в API"""
    class Config:
        from_attributes = True

class UserCache(UserBase):
    """Схема для кеширования в Redis"""
    last_updated: datetime
    permissions: list[str] = []

class UserInDB(UserBase):
    """Схема для хранения в PostgreSQL (может включать хеш пароля и другие приватные поля)"""
    hashed_password: str  # Если используется аутентификация
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True