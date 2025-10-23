from pydantic import BaseModel
from datetime import datetime

class ParticipantBase(BaseModel):
    event_id: int

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantRead(ParticipantBase):
    id: int
    user_id: str
    registered_at: datetime

    class Config:
        from_attributes = True
