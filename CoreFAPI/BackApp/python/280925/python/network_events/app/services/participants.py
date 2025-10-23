import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.event import EventRegistration, EventRegistrationCreate, EventRegistrationResponse
from app.utils.rabbitmq_events import send_participant_event
from app.models.event import Event
from app.exceptions.exceptions import EventNotFound, UserAlreadyRegistered, NoParticipantsFound, RegistrationNotFound
from datetime import datetime
from app.exceptions.error_handlers import handle_decorator, global_handle_error

logger = logging.getLogger("app")
class ParticipantService():
    def __init__(self, db: AsyncSession, current_user):
        self.db = db
        self.current_user = current_user

    @handle_decorator
    async def register_user_to_event(
        self, registration: EventRegistrationCreate) -> EventRegistrationResponse:
        # Регистрируем пользователя
        event = await self.db.get(Event, registration.event_id)

        if not event:
            await global_handle_error(EventNotFound, self.current_user.id, f"event с id {registration.event_id} не найден")

        registered = EventRegistration(event_id = registration.event_id, user_id = self.current_user.id, registered_at = datetime.utcnow())

        if await self.is_registered(registered.event_id):
            await global_handle_error(UserAlreadyRegistered, self.current_user.id, f"Данный пользователь уже зарегистрирован")

        self.db.add(registered)
        await self.db.commit()
        await self.db.refresh(registered)
            # Отправляем событие в RabbitMQ
        await send_participant_event("user_registered", registration.event_id, self.current_user.id)
        logger.info(f"User {self.current_user.id} registered for event {registration.event_id}")
        return registered
  
    @handle_decorator
    async def get_participants_for_event(self, event_id: int) -> list[EventRegistrationResponse]:
        # Получаем список участников
        result = await self.db.execute(
            select(EventRegistration).filter(EventRegistration.event_id == event_id)
        )
        participants = result.scalars().all()

        if not participants:
            await global_handle_error(NoParticipantsFound, self.current_user.id, "No Participants Found")

        logger.info(f"Fetched participants for event {event_id}")
        return participants
    
    @handle_decorator
    async def remove_participant_from_event(self, event_id: int) -> EventRegistrationResponse:
        # Удаляем пользователя из события

        registration = await self.is_registered(event_id)

        if not registration:
            await global_handle_error(RegistrationNotFound, self.current_user.id, "Registration Not Found")
                

        await self.db.delete(registration)
        await self.db.commit()

            # Отправляем событие в RabbitMQ
        await send_participant_event("user_unregistered", registration.event_id, self.current_user.id)

        logger.info(f"User {self.current_user.id} removed from event {event_id}")
        return registration
    
    ####PATTERNS####
    async def is_registered(self, event_id: int):
        result = await self.db.execute(select(EventRegistration).filter(EventRegistration.user_id == self.current_user.id, EventRegistration.event_id == event_id))

        event = result.scalars().first()
        return event
    ####PATTERNS####