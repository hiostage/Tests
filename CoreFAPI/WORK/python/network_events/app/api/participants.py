from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.event import EventRegistrationCreate, EventRegistrationResponse
from app.services.participants import ParticipantService
from app.services.user import UserService
from typing import List
import logging
from app.schemas.user import UserPublic
from app.utils.auth import get_current_user

logger = logging.getLogger("app")
router = APIRouter()

ERROR_500_INTERNAL = {"status_code": 500, "detail": "Internal Server Error"}

@router.post("/register", response_model=EventRegistrationResponse)
async def register_for_event(
    registration: EventRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user),
):
    logger.info(f"Запрос на регистрацию пользователя с ID {current_user.id} для события {registration.event_id}")

    participant_service = ParticipantService(db, current_user)
    # Используем сервис для регистрации
    registered = await participant_service.register_user_to_event(registration)
    logger.info(f"Пользователь с ID {current_user.id} успешно зарегистрирован для события {registration.event_id}")
    return registered

    

@router.get("/event/{event_id}/participants", response_model=List[EventRegistrationResponse])
async def get_event_participants(event_id: int, db: AsyncSession = Depends(get_db), current_user: UserPublic = Depends(get_current_user)):
    logger.info(f"Запрос на получение участников для события {event_id}")

    # Получаем участников события через сервис

    participant_service = ParticipantService(db, current_user)
    participants = await participant_service.get_participants_for_event(event_id)
    logger.info(f"Найдено {len(participants)} участников для события {event_id}")
    return participants




@router.delete("/event/{event_id}/participant", response_model=EventRegistrationResponse)
async def remove_participant_from_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user)
):
    logger.info(f"Запрос на удаление пользователя с ID {current_user.id} из события {event_id}")

    participant_service = ParticipantService(db, current_user)
    registration = await participant_service.remove_participant_from_event(event_id)
    logger.info(f"Пользователь с ID {current_user.id} успешно удалён из события {event_id}")
    return registration

