from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.event import EventCreate, EventRead
from app.services.events import EventService
import logging

router = APIRouter(prefix="/events", tags=["Events"])
logger = logging.getLogger("app")

@router.post("/", response_model=EventRead)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на создание события: {event}")
    try:
        created_event = await EventService.create_event(db, event)
        logger.info(f"Событие успешно создано: {created_event}")
        return created_event
    except Exception as e:
        logger.error(f"Ошибка при создании события: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании события")

@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на получение события с ID: {event_id}")
    event = await EventService.get_event(db, event_id)
    if not event:
        logger.warning(f"Событие с ID {event_id} не найдено")
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info(f"Событие с ID {event_id} найдено: {event}")
    return event

@router.get("/", response_model=list[EventRead])
async def list_events(db: AsyncSession = Depends(get_db)):
    logger.info("Запрос на получение списка всех событий")
    events = await EventService.list_events(db)
    logger.info(f"Найдено {len(events)} событий")
    return events

@router.delete("/{event_id}", response_model=EventRead)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на удаление события с ID: {event_id}")
    try:
        deleted_event = await EventService.delete_event(event_id, db)
        logger.info(f"Событие с ID {event_id} успешно удалено")
        return deleted_event
    except Exception as e:
        logger.error(f"Ошибка при удалении события с ID {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении события")
