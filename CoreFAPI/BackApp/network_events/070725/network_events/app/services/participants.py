import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.event import EventRegistration, EventRegistrationCreate, EventRegistrationResponse
from app.services.events import EventService
from app.utils.rabbitmq_events import send_participant_event
from fastapi import HTTPException
from app.services.user import UserService
from app.models.event import Event
from app.services.exceptions import *
from datetime import datetime
from app.utils.rabbitmq_events import send_event_event

logger = logging.getLogger(__name__)
class ParticipantService():
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user_to_event(
        self, registration: EventRegistrationCreate, user_id: str
    ) -> EventRegistrationResponse:
        # Регистрируем пользователя
        event = await self.db.get(Event, registration.event_id)

        if not event:
            await self.handle_error(EventNotFound, f"event с id {registration.event_id} не найден")


        registered = EventRegistration(event_id = registration.event_id, user_id = user_id, registered_at = datetime.utcnow())
        reg_test = select(EventRegistration).filter(EventRegistration.user_id == registered.user_id, EventRegistration.event_id == registered.event_id)
        result = await self.db.execute(reg_test)
        if result.scalars().first():
            await self.handle_error(UserAlreadyRegistered, f"Уже зареган")


        self.db.add(registered)
        await self.db.commit()
        await self.db.refresh(registered)
            # Отправляем событие в RabbitMQ
        await send_participant_event("user_registered", registration.event_id, user_id)
        logger.info(f"User {user_id} registered for event {registration.event_id}")
        return registered
  
    async def get_participants_for_event(
        self, event_id: int
    ) -> list[EventRegistrationResponse]:
        # Получаем список участников
        result = await self.db.execute(
            select(EventRegistration).filter(EventRegistration.event_id == event_id)
        )
        participants = result.scalars().all()

        if not participants:
            await self.handle_error(NoParticipantsFound)

        logger.info(f"Fetched participants for event {event_id}")
        return participants
 
    async def remove_participant_from_event(
        self, event_id: int, user_id: str
    ) -> EventRegistrationResponse:
        # Удаляем пользователя из события
        result = await self.db.execute(
            select(EventRegistration).filter(EventRegistration.event_id == event_id, EventRegistration.user_id == user_id)
        )
        registration = result.scalar_one_or_none()

        if not registration:
            await self.handle_error(RegistrationNotFound)
                

        await self.db.delete(registration)
        await self.db.commit()

            # Отправляем событие в RabbitMQ
        await send_participant_event("user_unregistered", registration.event_id, user_id)

        logger.info(f"User {user_id} removed from event {event_id}")
        return registration
            
        
    async def handle_error(self, exeption_cls: type[Exception], log_message: int = None):
        logger.error(log_message)
        raise exeption_cls()