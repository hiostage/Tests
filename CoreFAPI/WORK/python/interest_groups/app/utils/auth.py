from fastapi import Depends, Request, HTTPException
import httpx
from app.core.config import settings
from app.schemas.user import UserPublic, UserFull
from app.utils.logger import logger

async def get_current_user(request: Request) -> UserFull:
    """Получаем текущего пользователя из сессии"""
    session_id = request.cookies.get("sessionId")
    if not session_id:
        logger.warning("Session ID is missing in request cookies.")
        raise HTTPException(status_code=401, detail="Session required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_PROXY_URL}user",
                cookies={"sessionId": session_id},
                timeout=5.0
            )
            if response.status_code != 200:
                logger.warning(f"Invalid session for session ID {session_id}. Response code: {response.status_code}")
                raise HTTPException(status_code=401, detail="Invalid session")
            data = response.json()
            user_data = {
                "id": data["uuid"],  # переименовываем
                "username": data["userName"],
                "first_name": data["firstName"],
                "last_name": data["lastName"],
                "email": data.get("email", "no@email.local"),  # если email нет — подставляем дефолт
                "is_active": data.get("is_active", True),
                "created_at": data.get("created_at", None),
            }
            logger.info(f"User {user_data['username']} retrieved successfully.")
            return UserFull(**user_data)
    except httpx.RequestError as e:
        logger.error(f"Error while checking session for session ID {session_id}: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
