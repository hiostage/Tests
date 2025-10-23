from fastapi import Depends, Request, HTTPException
import httpx
from app.core.config import settings
from app.schemas.user import UserPublic
from app.utils.logger import logger

async def get_current_user(request: Request):
    """Получаем текущего пользователя из сессии"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.warning("Session ID is missing in request cookies.")
        raise HTTPException(status_code=401, detail="Session required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_PROXY_URL}check_session",  # Путь с сессией
                cookies={"session_id": session_id},  # Передаем session_id в cookies
                timeout=5.0
            )
            if response.status_code != 200:
                logger.warning(f"Invalid session. Response code: {response.status_code}")
                raise HTTPException(status_code=401, detail="Invalid session")
            logger.info(f"Session {session_id} is valid.")
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error while checking session for session ID {session_id}: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")


async def get_current_user_for_posts(request: Request) -> UserPublic:
    """Получаем текущего пользователя из сессии"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        logger.warning("Session ID is missing in request cookies.")
        raise HTTPException(status_code=401, detail="Session required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_PROXY_URL}check_session",
                cookies={"session_id": session_id},
                timeout=5.0
            )
            if response.status_code != 200:
                logger.warning(f"Invalid session for session ID {session_id}. Response code: {response.status_code}")
                raise HTTPException(status_code=401, detail="Invalid session")
            data = response.json()
            user_data = {
                "id": data["user_id"],  # переименовываем
                "username": data["username"],
                "email": data.get("email", "no@email.local"),  # если email нет — подставляем дефолт
                "is_active": data["is_active"],
                "created_at": data.get("created_at", None),
            }
            logger.info(f"User {user_data['username']} retrieved successfully.")
            return UserPublic(**user_data)
    except httpx.RequestError as e:
        logger.error(f"Error while checking session for session ID {session_id}: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
