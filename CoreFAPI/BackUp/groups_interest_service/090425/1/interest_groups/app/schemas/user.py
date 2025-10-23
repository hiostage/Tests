from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Минимальная схема пользователя только для чтения"""
    id: int
    username: str
    email: Optional[str]
    is_active: bool = True
    created_at: Optional[datetime] = None  # Добавление даты создания
    updated_at: Optional[datetime] = None  # Добавление даты обновления

    class Config:
        from_attributes = True  # Новая настройка для работы с ORM в Pydantic v2

class UserPublic(UserBase):
    """Публичная схема для отдачи в API"""
    class Config:
        from_attributes = True

class UserCache(UserBase):
    """Схема для кеширования в Redis"""
    last_updated: datetime
    permissions: list[str] = []

class UserInDB(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool = True
    permissions: list[str] = []

    # Сделать необязательными:
    hashed_password: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None