from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.schemas.event import EventCreate
from sqlalchemy import select, delete

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import EventRegistration
from app.models.event import Event
from app.utils.rabbitmq_events import send_event_event
import logging
from app.exceptions.exceptions import EventNotFound
from app.exceptions.error_handlers import handle_decorator, global_handle_error

logger = logging.getLogger("app")
class EventService():
    def __init__(self, db: AsyncSession, current_user):
        self.current_user = current_user
        self.db = db

    @handle_decorator
    async def create_event(self, event_data: EventCreate) -> Event:
        logger.info(f"Создание нового события с данными: {event_data}")

        event = Event(**event_data.model_dump())
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        await send_event_event(event.id, "event_created")   

        logger.info(f"Событие с ID {event.id} успешно создано")
        return event

    @handle_decorator
    async def get_event(self, event_id: int) -> Event | None:
        logger.info(f"Запрос события с ID {event_id}")
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if not event:
            await global_handle_error(EventNotFound, self.current_user.id, f"События с ID: {event_id}, не найдено")
        
        return event
    
    @handle_decorator
    async def list_events(self) -> list[Event]:
        logger.info("Запрос списка всех событий")
        result = await self.db.execute(select(Event))
        events = result.scalars().all()
        logger.info(f"Найдено {len(events)} событий")
        return events
    
    @handle_decorator
    async def delete_event(self, event_id: int):
        logger.info(f"Попытка удалить событие с ID {event_id}")

        event = await self.get_event(event_id)

        # Удаляем все регистрации на это событие
        await self.db.execute(
            delete(EventRegistration).where(EventRegistration.event_id == event_id)
        )
        logger.info(f"Удалены все регистрации для события с ID {event_id}")

        # Теперь удаляем само событие
        await self.db.delete(event)
        await self.db.commit()
        await send_event_event(event_id, "event_deleted")

        logger.info(f"Событие с ID {event_id} успешно удалено")
        return event
