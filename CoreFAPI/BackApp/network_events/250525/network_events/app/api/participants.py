from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.event import EventRegistrationCreate, EventRegistrationResponse
from app.services.participants import ParticipantService
from app.services.user import UserService
from typing import List
import logging

logger = logging.getLogger("app")
router = APIRouter()

@router.post("/register", response_model=EventRegistrationResponse)
async def register_for_event(
    registration: EventRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(UserService.get_user_id_from_session),
):
    logger.info(f"Запрос на регистрацию пользователя с ID {user_id} для события {registration.event_id}")

    if not user_id:
        logger.warning(f"Попытка регистрации неавторизованного пользователя для события {registration.event_id}")
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Используем сервис для регистрации
    try:
        registered = await ParticipantService.register_user_to_event(db, registration, user_id)
        logger.info(f"Пользователь с ID {user_id} успешно зарегистрирован для события {registration.event_id}")
        return registered
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя с ID {user_id} для события {registration.event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.get("/event/{event_id}/participants", response_model=List[EventRegistrationResponse])
async def get_event_participants(event_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на получение участников для события {event_id}")

    # Получаем участников события через сервис
    try:
        participants = await ParticipantService.get_participants_for_event(event_id, db)
        logger.info(f"Найдено {len(participants)} участников для события {event_id}")
        return participants
    except Exception as e:
        logger.error(f"Ошибка при получении участников для события {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get participants")

@router.delete("/event/{event_id}/participant", response_model=EventRegistrationResponse)
async def remove_participant_from_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(UserService.get_user_id_from_session)
):
    logger.info(f"Запрос на удаление пользователя с ID {user_id} из события {event_id}")

    if not user_id:
        logger.warning(f"Попытка удалить неавторизованного пользователя для события {event_id}")
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Используем сервис для удаления участника
    try:
        registration = await ParticipantService.remove_participant_from_event(event_id, user_id, db)
        logger.info(f"Пользователь с ID {user_id} успешно удалён из события {event_id}")
        return registration
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователя с ID {user_id} из события {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove participant")
