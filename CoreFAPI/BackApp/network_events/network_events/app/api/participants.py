from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.event import EventRegistrationCreate, EventRegistrationResponse
from app.services.events import EventService
from app.services.user import UserService



router = APIRouter()

@router.post("/register", response_model=EventRegistrationResponse)
async def register_for_event(
    registration: EventRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(UserService.get_user_id_from_session),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return await EventService.register_user_to_event(db=db, event_id=registration.event_id, user_id=user_id)
