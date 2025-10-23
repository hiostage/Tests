from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.event import EventCreate, EventRead
from app.services.events import EventService
import logging
from app.utils.auth import get_current_user
from app.schemas.user import UserPublic

router = APIRouter(prefix="/events", tags=["Events"])
logger = logging.getLogger("app")

ERROR_500_INTERNAL = {"status_code": 500, "detail": "Internal Server Error"}

@router.post("/", response_model=EventRead)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db), current_user: UserPublic = Depends(get_current_user)):
    logger.info(f"Запрос на создание события: {event}")

    event_service = EventService(db, current_user)
    created_event = await event_service.create_event(event_data=event)
    logger.info(f"Событие успешно создано: {created_event}")
    return created_event



@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db), current_user: UserPublic = Depends(get_current_user)):
    logger.info(f"Запрос на получение события с ID: {event_id}")

    event_service = EventService(db, current_user)
    event = await event_service.get_event(event_id)
    return event
    

@router.get("/", response_model=list[EventRead])
async def list_events(db: AsyncSession = Depends(get_db), current_user: UserPublic = Depends(get_current_user)):

    logger.info("Запрос на получение списка всех событий")
    event_service = EventService(db, current_user)
    events = await event_service.list_events()
    logger.info(f"Найдено {len(events)} событий")
    return events



@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db), current_user: UserPublic = Depends(get_current_user)):
    logger.info(f"Запрос на удаление события с ID: {event_id}")

    event_service = EventService(db, current_user)
    deleted_event = await event_service.delete_event(event_id)
    logger.info(f"Событие с ID {event_id} успешно удалено")
    return 

