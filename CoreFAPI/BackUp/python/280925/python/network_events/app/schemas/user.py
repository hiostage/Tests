from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    id: str = Field(alias = "uuid")
    username: str = Field(alias = "userName")
    email: Optional[str]
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        from_attributes = True

class UserPublic(UserBase):
    first_name: str = Field(alias = "firstName")
    last_name: str = Field(alias = "lastName")
    phone: Optional[str] = None
    roles: Optional[List[str]] = None

    class Config:
        from_attributes = True

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
