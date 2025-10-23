from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserPublic  # Используем публичную схему пользователя

class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, example="Интересный пост")
    content: str = Field(..., min_length=10, example="Подробное содержание поста...")
    group_id: int = Field(..., example=1)

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values
    
    
class Post(PostBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    author_id: int
    is_pinned: bool = False
    tags: List[str] = []
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Пример поста",
                "content": "Содержание поста...",
                "group_id": 1,
                "author_id": 1,
                "created_at": "2023-01-01T00:00:00",
                "is_pinned": False,
                "tags": ["технологии", "программирование"]
            }
        }
    )

class PostWithAuthor(Post):
    author: UserPublic  # Используем UserPublic вместо UserBase
    views_count: int = Field(0, ge=0, example=42)
    comments_count: int = Field(0, ge=0, example=5)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                **Post.model_config.get("json_schema_extra", {}),
                "author": {
                    "id": 1,
                    "username": "test_user",
                    "email": "user@example.com",
                    "is_active": True
                },
                "views_count": 100,
                "comments_count": 5
            }
        }
    )

class PostInDB(Post):
    """Схема для внутреннего использования с дополнительными полями"""
    edited_by: Optional[int] = None
    edit_reason: Optional[str] = None

class PostList(BaseModel):
    posts: List[PostWithAuthor]
    total: int
    limit: int
    offset: int
