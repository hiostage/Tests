import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.event import EventRegistration, EventRegistrationCreate, EventRegistrationResponse
from app.services.events import EventService
from app.utils.rabbitmq_events import send_participant_event
from fastapi import HTTPException
from app.services.user import UserService

logger = logging.getLogger(__name__)
class ParticipantService:
    @staticmethod
    async def register_user_to_event(
        db: AsyncSession, registration: EventRegistrationCreate, user_id: int
    ) -> EventRegistrationResponse:
        # Регистрируем пользователя
        try:
            registered = await EventService.register_user_to_event(
                db=db, event_id=registration.event_id, user_id=user_id
            )

            # Отправляем событие в RabbitMQ
            await send_participant_event("user_registered", registration.event_id, user_id)
            logger.info(f"User {user_id} registered for event {registration.event_id}")
            return registered
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            raise HTTPException(status_code=500, detail="Error during registration")
  
    @staticmethod
    async def get_participants_for_event(
        event_id: int, db: AsyncSession
    ) -> list[EventRegistrationResponse]:
        # Получаем список участников
        result = await db.execute(
            select(EventRegistration).filter(EventRegistration.event_id == event_id)
        )
        participants = result.scalars().all()

        if not participants:
            raise HTTPException(status_code=404, detail="No participants found for this event")

        logger.info(f"Fetched participants for event {event_id}")
        return participants
 
    @staticmethod
    async def remove_participant_from_event(
        event_id: int, user_id: int, db: AsyncSession
    ) -> EventRegistrationResponse:
        # Удаляем пользователя из события
        try:
            result = await db.execute(
                select(EventRegistration).filter(EventRegistration.event_id == event_id, EventRegistration.user_id == user_id)
            )
            registration = result.scalar_one_or_none()

            if not registration:
                raise HTTPException(status_code=404, detail="Registration not found")

            await db.delete(registration)
            await db.commit()

            # Отправляем событие в RabbitMQ
            await send_participant_event("user_unregistered", registration.event_id, user_id)

            logger.info(f"User {user_id} removed from event {event_id}")
            return registration
        except Exception as e:
            logger.error(f"Error during unregistration: {str(e)}")
            raise HTTPException(status_code=500, detail="Error during unregistration")
