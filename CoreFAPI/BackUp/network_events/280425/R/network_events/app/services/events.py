from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.schemas.event import EventCreate
from sqlalchemy import select, delete
from datetime import datetime
from app.db.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import EventRegistration
from app.models.event import Event
from app.services.user import UserService
from fastapi import HTTPException, status, Depends
from app.utils.rabbitmq_events import send_event_event

class EventService:
    @staticmethod
    async def register_user_to_event(db: AsyncSession, event_id: int, user_id: int) -> EventRegistration:
        event = await db.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        existing_registration = await db.execute(select(EventRegistration).filter_by(event_id=event_id, user_id=user_id))
        if existing_registration.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")

        registration = EventRegistration(event_id=event_id, user_id=user_id, registered_at=datetime.utcnow())
        db.add(registration)
        await db.commit()
        await db.refresh(registration)

        return registration

    @staticmethod
    async def create_event(db: AsyncSession, event_data: EventCreate) -> Event:
        event = Event(**event_data.model_dump())
        db.add(event)
        await db.commit()
        await db.refresh(event)
        await send_event_event(event.id, "event_created")   
        
        return event
    
    

    @staticmethod
    async def get_event(db: AsyncSession, event_id: int) -> Event | None:
        result = await db.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_events(db: AsyncSession) -> list[Event]:
        result = await db.execute(select(Event))
        return result.scalars().all()

    @staticmethod
    async def delete_event(event_id: int, db: AsyncSession):
        event = await EventService.get_event(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Удаляем все регистрации на это событие
        await db.execute(
            delete(EventRegistration).where(EventRegistration.event_id == event_id)
        )

        # Теперь удаляем само событие
        await db.delete(event)
        await db.commit()
        await send_event_event(event_id, "event_deleted")

        return event
