from pydantic import BaseModel

class LikeSchema(BaseModel):
    user_id: int
    post_id: int

class CommentSchema(BaseModel):
    user_id: int
    post_id: int
    text: str

class RepostSchema(BaseModel):
    user_id: int
    post_id: int
