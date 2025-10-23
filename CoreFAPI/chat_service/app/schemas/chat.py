from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Схема для создания чата
class ChatCreate(BaseModel):
    name: Optional[str] = None
    is_group: bool

# Схема ответа (то, что вернется из API)
class ChatResponse(BaseModel):
    id: int
    name: Optional[str] = None
    is_group: bool
    created_at: datetime

    class Config:
        from_attributes = True
