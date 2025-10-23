from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.event import EventRegistrationCreate, EventRegistrationResponse
from app.services.events import EventService
from app.services.user import UserService
from app.models.event import EventRegistrationResponse
from app.models.event import EventRegistration
from sqlalchemy.future import select
from typing import List
from app.utils.rabbitmq_events import send_participant_event

router = APIRouter()



@router.post("/register", response_model=EventRegistrationResponse)
async def register_for_event(
    registration: EventRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(UserService.get_user_id_from_session),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Сначала регистрируем пользователя
    registered = await EventService.register_user_to_event(
        db=db, event_id=registration.event_id, user_id=user_id
    )

    # Потом отправляем событие в RabbitMQ
    await send_participant_event("user_registered", registration.event_id, user_id)

    return registered

@router.get("/event/{event_id}/participants", response_model=List[EventRegistrationResponse])
async def get_event_participants(event_id: int, db: AsyncSession = Depends(get_db)):
    # Получаем всех зарегистрированных пользователей для указанного события
    result = await db.execute(select(EventRegistration).filter(EventRegistration.event_id == event_id))
    participants = result.scalars().all()

    if not participants:
        raise HTTPException(status_code=404, detail="No participants found for this event")

    return participants

@router.delete("/event/{event_id}/participant", response_model=EventRegistrationResponse)
async def remove_participant_from_event(event_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(UserService.get_user_id_from_session)):
    # Проверяем, что пользователь авторизован
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Ищем регистрацию пользователя на событие
    result = await db.execute(
        select(EventRegistration).filter(EventRegistration.event_id == event_id, EventRegistration.user_id == user_id)
    )
    registration = result.scalar_one_or_none()

    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Удаляем запись о регистрации
    await db.delete(registration)
    await db.commit()

    await send_participant_event("user_unregistered", registration.event_id, user_id)

    # Возвращаем информацию о пользователе, который отписался
    return registration
