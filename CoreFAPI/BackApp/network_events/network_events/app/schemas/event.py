from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List

class EventBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    location: str | None = None
    is_online: bool = False
    start_time: datetime = Field(default_factory=lambda: datetime.utcnow())
    end_time: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))

class EventCreate(EventBase):
    pass

class EventRead(EventBase):
    id: int
    created_at: datetime
    registered_user_ids: List[int]  # Добавляем список ID пользователей

    class Config:
        from_attributes = True
