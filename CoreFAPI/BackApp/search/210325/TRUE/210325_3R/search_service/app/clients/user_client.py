import httpx
from app.schemas.user import User

class UserClient:
    @staticmethod
    async def get_users():
        async with httpx.AsyncClient() as client:
            response = await client.get("http://user-service:8000/users")
            response.raise_for_status()
            return [User(**user) for user in response.json()]