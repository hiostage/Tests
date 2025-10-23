from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.schemas.event import EventCreate
from sqlalchemy import select
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import EventRegistration
from app.models.event import Event
from app.services.user import UserService
from fastapi import HTTPException, status

class EventService:
    @staticmethod
    async def register_user_to_event(db: AsyncSession, event_id: int, user_id: int) -> EventRegistration:
        # Проверяем, существует ли событие
        event = await db.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        # Проверяем, не зарегистрирован ли пользователь
        existing_registration = await db.execute(select(EventRegistration).filter_by(event_id=event_id, user_id=user_id))
        if existing_registration.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")

        # Регистрируем пользователя
        registration = EventRegistration(event_id=event_id, user_id=user_id, registered_at=datetime.utcnow())
        db.add(registration)
        await db.commit()
        await db.refresh(registration)

        return registration


    async def create_event(session: AsyncSession, event_data: EventCreate) -> Event:
        event = Event(**event_data.model_dump())
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    async def get_event(session: AsyncSession, event_id: int) -> Event | None:
        result = await session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def list_events(session: AsyncSession) -> list[Event]:
        result = await session.execute(select(Event))
        return result.scalars().all()
