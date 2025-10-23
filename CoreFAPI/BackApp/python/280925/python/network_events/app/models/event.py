from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    location = Column(String)
    is_online = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    registrations = relationship("EventRegistration", back_populates="event")

class EventRegistration(Base):
    __tablename__ = 'event_registrations'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    user_id = Column(String, nullable=False)
    registered_at = Column(DateTime, nullable=False)

    event = relationship("Event", back_populates="registrations")


class EventRegistrationCreate(BaseModel):
    event_id: int

class EventRegistrationResponse(BaseModel):
    id: int
    event_id: int
    user_id: str
    registered_at: datetime

    class Config:
        orm_mode = True