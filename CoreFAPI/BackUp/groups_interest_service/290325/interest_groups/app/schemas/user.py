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
        orm_mode = True

class UserCache(UserBase):
    """Схема для кеширования в Redis"""
    last_updated: datetime
    permissions: list[str] = []