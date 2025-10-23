from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.user import UserService
from app.schemas.user import UserInDB


async def get_current_user_full(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserInDB:
    user = await UserService.get_or_fetch_user(db, request)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
