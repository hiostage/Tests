from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    id: str
    username: str
    email: Optional[str]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserPublic(UserBase):
    """Публичная схема для отдачи в API"""
    pass

class UserCache(UserBase):
    last_updated: datetime
    permissions: List[str] = Field(default_factory=list)

class UserInDB(UserBase):
    first_name: str
    last_name: str
    username: str
    email: str
    phone: Optional[str] = None
    roles: Optional[List[str]] = None
