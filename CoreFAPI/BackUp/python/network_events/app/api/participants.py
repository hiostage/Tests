from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.event import EventRegistrationCreate, EventRegistrationResponse
from app.services.participants import ParticipantService
from app.services.user import UserService
from typing import List
import logging
from app.services.exceptions import *


logger = logging.getLogger("app")
router = APIRouter()

@router.post("/register", response_model=EventRegistrationResponse)
async def register_for_event(
    registration: EventRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(UserService.get_user_id_from_session),
):
    logger.info(f"Запрос на регистрацию пользователя с ID {user_id} для события {registration.event_id}")

    if not user_id:
        logger.warning(f"Попытка регистрации неавторизованного пользователя для события {registration.event_id}")
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Используем сервис для регистрации
    try:
        participant_service = ParticipantService(db)
        registered = await participant_service.register_user_to_event(registration, user_id)
        logger.info(f"Пользователь с ID {user_id} успешно зарегистрирован для события {registration.event_id}")
        return registered
    except UserAlreadyRegistered:
        logger.error(f"User already registered")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")
    except EventNotFound:
        logger.error(f"Event Not Found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event Not Found")
    except ErrorDuringRegistration:
        logger.error(f"Error during registration")
        raise HTTPException(status_code=500, detail="Error during registration")
    

@router.get("/event/{event_id}/participants", response_model=List[EventRegistrationResponse])
async def get_event_participants(event_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на получение участников для события {event_id}")

    # Получаем участников события через сервис
    try:
        participant_service = ParticipantService(db)
        participants = await participant_service.get_participants_for_event(event_id)
        logger.info(f"Найдено {len(participants)} участников для события {event_id}")
        return participants
    except NoParticipantsFound:
        logger.error(f"Ошибка при получении участников для события {event_id}")
        raise HTTPException(status_code=404, detail="No participants found for this event")


@router.delete("/event/{event_id}/participant", response_model=EventRegistrationResponse)
async def remove_participant_from_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(UserService.get_user_id_from_session)
):
    logger.info(f"Запрос на удаление пользователя с ID {user_id} из события {event_id}")

    if not user_id:
        logger.warning(f"Попытка удалить неавторизованного пользователя для события {event_id}")
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Используем сервис для удаления участника
    try:
        participant_service = ParticipantService(db)
        registration = await participant_service.remove_participant_from_event(event_id, user_id)
        logger.info(f"Пользователь с ID {user_id} успешно удалён из события {event_id}")
        return registration
    except RegistrationNotFound:
        logger.error(f"Ошибка при удалении пользователя с ID {user_id} из события {event_id}")
        raise HTTPException(status_code=404, detail="Registration not found")
