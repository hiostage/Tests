from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from enum import Enum
from app.schemas.user import UserPublic  # Используем публичную схему пользователя

class GroupCategory(str, Enum):
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    ART = "art"
    EDUCATION = "education"
    OTHER = "other"

class GroupBase(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Название группы",
        json_schema_extra={
            "example": "Python Developers"  # Новый формат
        }
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        example="Группа для разработчиков на Python",
        description="Описание группы"
    )
    category: GroupCategory = Field(
        default=GroupCategory.TECHNOLOGY,
        example="technology",
        description="Категория группы"
    )
    is_public: bool = Field(
        default=True,
        example=True,
        description="Видимость группы для всех пользователей"
    )

    @validator('name')
    def name_must_contain_letters(cls, v):
        if not any(c.isalpha() for c in v):
            raise ValueError('Название должно содержать буквы')
        return v

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[GroupCategory]
    is_public: Optional[bool]
    banner_url: Optional[str] = Field(None, example="https://example.com/banner.jpg")

class Group(GroupBase):
    id: int = Field(..., example=1)
    creator_id: int = Field(..., example=1)
    created_at: datetime = Field(..., example="2023-01-01T00:00:00")
    updated_at: Optional[datetime] = Field(None, example="2023-01-02T00:00:00")
    member_count: int = Field(0, ge=0, example=42)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Python Developers",
                "description": "Группа для разработчиков на Python",
                "category": "technology",
                "is_public": True,
                "creator_id": 1,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "member_count": 42
            }
        }

class GroupWithMembers(Group):
    creator: UserPublic  # Используем публичную схему пользователя
    members: List[UserPublic] = Field([], description="Список участников группы")
    is_member: Optional[bool] = Field(
        None, 
        description="Принадлежит ли текущий пользователь к группе"
    )
    
    class Config:
        from_attributes = True  # Добавляем для работы с ORM
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Python Developers",
                "description": "Group for Python programmers",
                "is_public": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "creator": {
                    "id": 1,
                    "username": "python_dev",
                    "email": "dev@example.com",
                    "is_active": True
                },
                "members": [
                    {
                        "id": 2,
                        "username": "user2",
                        "email": "user2@example.com",
                        "is_active": True
                    }
                ],
                "is_member": True
            }
        }
        
class GroupList(BaseModel):
    """Схема для пагинированного списка групп"""
    groups: List[Group]
    total: int = Field(..., example=100)
    limit: int = Field(..., example=10)
    offset: int = Field(..., example=0)