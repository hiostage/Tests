from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.event import EventCreate, EventRead
from app.services.events import EventService
import logging
from app.services.exceptions import *

router = APIRouter(prefix="/events", tags=["Events"])
logger = logging.getLogger("app")

@router.post("/", response_model=EventRead)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на создание события: {event}")
    try:
        event_service = EventService(db)
        created_event = await event_service.create_event(event_data=event)
        logger.info(f"Событие успешно создано: {created_event}")
        return created_event
    except Exception as e:
        logger.error(f"Ошибка при создании события: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании события")


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на получение события с ID: {event_id}")
    try:
        event_service = EventService(db)
        event = await event_service.get_event(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/", response_model=list[EventRead])
async def list_events(db: AsyncSession = Depends(get_db)):
    logger.info("Запрос на получение списка всех событий")
    event_service = EventService(db)
    events = await event_service.list_events()
    logger.info(f"Найдено {len(events)} событий")
    return events

@router.delete("/{event_id}", response_model=EventRead)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Запрос на удаление события с ID: {event_id}")
    try:
        event_service = EventService(db)
        deleted_event = await event_service.delete_event(event_id)
        logger.info(f"Событие с ID {event_id} успешно удалено")
        return deleted_event
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event Not Found")
