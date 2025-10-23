from pydantic import BaseModel
from datetime import datetime

class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] = []
    is_private: bool = False

class GroupResponse(GroupCreate):
    id: int
    creator_id: int
    created_at: datetime

class PostCreate(BaseModel):
    group_id: int
    author_id: int
    content: str

class PostResponse(PostCreate):
    id: int
    created_at: datetime

class CommentCreate(BaseModel):
    post_id: int
    author_id: int
    text: str

class CommentResponse(CommentCreate):
    id: int
    created_at: datetime