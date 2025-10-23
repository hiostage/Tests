from fastapi import Depends, Request, HTTPException
import httpx
from app.core.config import settings
from app.schemas.user import UserPublic


async def get_current_user(request: Request):
    """Получаем текущего пользователя из сессии"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Session required")
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_PROXY_URL}check_session",  # Путь с сессией
                cookies={"session_id": session_id},  # Передаем session_id в cookies
                timeout=5.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    


async def get_current_user_for_posts(request: Request) -> UserPublic:
    """Получаем текущего пользователя из сессии"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Session required")
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_PROXY_URL}check_session",
                cookies={"session_id": session_id},
                timeout=5.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            data = response.json()
            user_data = {
                "id": data["user_id"],  # переименовываем
                "username": data["username"],
                "email": data.get("email", "no@email.local"),  # если email нет — подставляем дефолт
                "is_active": data["is_active"],
                "created_at": data.get("created_at", None),
            }
            return UserPublic(**user_data)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")