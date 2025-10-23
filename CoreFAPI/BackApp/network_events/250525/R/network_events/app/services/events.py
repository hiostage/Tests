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
import logging

logger = logging.getLogger("app")
class EventService:
    @staticmethod
    async def register_user_to_event(db: AsyncSession, event_id: int, user_id: str) -> EventRegistration:
        logger.info(f"Попытка зарегистрировать пользователя с ID {user_id} на событие {event_id}")

        event = await db.get(Event, event_id)
        if not event:
            logger.error(f"Событие с ID {event_id} не найдено для регистрации пользователя {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        existing_registration = await db.execute(select(EventRegistration).filter_by(event_id=event_id, user_id=user_id))
        if existing_registration.scalars().first():
            logger.warning(f"Пользователь с ID {user_id} уже зарегистрирован на событие {event_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")

        registration = EventRegistration(event_id=event_id, user_id=user_id, registered_at=datetime.utcnow())
        db.add(registration)
        await db.commit()
        await db.refresh(registration)

        logger.info(f"Пользователь с ID {user_id} успешно зарегистрирован на событие {event_id}")
        return registration

    @staticmethod
    async def create_event(db: AsyncSession, event_data: EventCreate) -> Event:
        logger.info(f"Создание нового события с данными: {event_data}")

        event = Event(**event_data.model_dump())
        db.add(event)
        await db.commit()
        await db.refresh(event)
        await send_event_event(event.id, "event_created")   

        logger.info(f"Событие с ID {event.id} успешно создано")
        return event

    @staticmethod
    async def get_event(db: AsyncSession, event_id: int) -> Event | None:
        logger.info(f"Запрос события с ID {event_id}")
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if event:
            logger.info(f"Событие с ID {event_id} найдено")
        else:
            logger.warning(f"Событие с ID {event_id} не найдено")
        
        return event

    @staticmethod
    async def list_events(db: AsyncSession) -> list[Event]:
        logger.info("Запрос списка всех событий")
        result = await db.execute(select(Event))
        events = result.scalars().all()
        logger.info(f"Найдено {len(events)} событий")
        return events

    @staticmethod
    async def delete_event(event_id: int, db: AsyncSession):
        logger.info(f"Попытка удалить событие с ID {event_id}")

        event = await EventService.get_event(db, event_id)
        if not event:
            logger.error(f"Событие с ID {event_id} не найдено для удаления")
            raise HTTPException(status_code=404, detail="Event not found")

        # Удаляем все регистрации на это событие
        await db.execute(
            delete(EventRegistration).where(EventRegistration.event_id == event_id)
        )
        logger.info(f"Удалены все регистрации для события с ID {event_id}")

        # Теперь удаляем само событие
        await db.delete(event)
        await db.commit()
        await send_event_event(event_id, "event_deleted")

        logger.info(f"Событие с ID {event_id} успешно удалено")
        return event