from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserPublic  # Используем публичную схему пользователя
from app.utils.logger import logger

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
    author_id: str
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

    @classmethod
    def from_orm(cls, obj):
        # Проверка критичных полей перед сериализацией
        if obj.group_id is None:
            logger.warning(f"Post ID {getattr(obj, 'id', 'unknown')} has no group_id. Skipping.")
            raise ValueError("Post must have a valid group_id.")

        if getattr(obj, "author", None) is None:
            logger.warning(f"Post ID {getattr(obj, 'id', 'unknown')} has no author loaded.")
            raise ValueError("Post must have an author.")

        return super().from_orm(obj)

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
    edited_by: Optional[str] = None
    edit_reason: Optional[str] = None

class PostList(BaseModel):
    posts: List[PostWithAuthor]
    total: int
    limit: int
    offset: int
