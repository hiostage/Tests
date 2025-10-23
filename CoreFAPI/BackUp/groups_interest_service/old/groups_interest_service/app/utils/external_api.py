import httpx
from fastapi import HTTPException
from app.config.settings import settings

async def get_user_info(user_id: int):
    """Запрос информации о пользователе из внешнего сервиса"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/users/{user_id}",
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=404,
                detail="User not found in external service"
            )