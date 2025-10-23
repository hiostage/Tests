from fastapi import Request, Depends, HTTPException
from fastapi.security import HTTPBearer
import httpx
from app.core.config import settings

async def validate_session(request: Request):
    """Проверка сессии через auth_proxy"""
    session_cookie = request.cookies.get("session_id")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Session required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_PROXY_URL}/check_session",
                cookies={"session_id": session_cookie},
                headers={"X-Real-IP": request.client.host}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

def get_current_user(request: Request):
    """Зависимость для получения текущего пользователя"""
    return validate_session(request)