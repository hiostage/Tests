from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.event import EventCreate, EventRead
from app.services.events import EventService
from app.main import logger

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("/", response_model=EventRead)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Создание события: {event}")
    return await EventService.create_event(db, event)

@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    event = await EventService.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/", response_model=list[EventRead])
async def list_events(db: AsyncSession = Depends(get_db)):
    return await EventService.list_events(db)

@router.delete("/{event_id}", response_model=EventRead)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db)):
    return await EventService.delete_event(event_id, db)
