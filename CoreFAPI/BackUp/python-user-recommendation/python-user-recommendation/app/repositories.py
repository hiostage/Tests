from sqlalchemy import select
from app.models import User
from app.db.databse import get_async_session


class UserRepository:
    async def get_user_by_id(self, user_id: int):
        async with get_async_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            return result.scalars().first()

    async def get_all_users(self):
        async with get_async_session() as session:
            query = select(User)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_users_by_purpose_cooperation(self, purpose_cooperation: str):
        async with get_async_session() as session:
            query = select(User).where(User.purpose_cooperation == purpose_cooperation)
            result = await session.execute(query)
            return result.scalars().all()
