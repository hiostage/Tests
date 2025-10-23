import httpx
from typing import List, Optional
from fastapi import HTTPException


REGSERV_URL = "http://mock_auth:8010"


class ExternalUserClient:
    def __init__(self):
        self.base_url = REGSERV_URL

    async def get_current_user(self, session_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user",
                cookies={"sessionId": session_id},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=401, detail="Неверная сессия")

    async def get_all_users(self) -> List[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/all",  # предполагаем, что такой эндпоинт нужен
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=500, detail="Ошибка получения пользователей")
