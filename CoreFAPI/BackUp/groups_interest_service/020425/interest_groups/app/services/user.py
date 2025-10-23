from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional, List, Dict
import httpx
from app.models.user import User
from app.schemas.user import UserBase, UserInDB
from app.core.config import settings
from app.utils.logger import logger
from app.utils.cache import cache  # Предполагаем наличие кеша
from datetime import datetime, timedelta
from sqlalchemy.future import select

class UserService:
    @staticmethod
    @cache.cached(ttl=timedelta(minutes=5), key_prefix="user_data")
    async def get_user_from_auth_service(user_id: int) -> Optional[UserInDB]:
        """
        Получение данных пользователя из внешнего сервиса с кешированием.
        Возвращает UserInDB с полной информацией о пользователе.
        """
        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{settings.AUTH_SERVICE_URL}/api/v1/users/{user_id}",
                    headers={
                        "Authorization": f"Bearer {settings.AUTH_SERVICE_TOKEN}",
                        "X-Request-ID": str(hash(user_id))[:8]  # Для трассировки
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Fetched user data: {data}")
                    return UserInDB(**data)
                
                logger.error(f"User service error: {response.status_code} - {response.text}")
        except httpx.TimeoutException:
            logger.error("User service request timeout")
        except Exception as e:
            logger.error(f"User service connection error: {str(e)}")
            
        return None

    @staticmethod
    async def get_local_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Получение локальной копии пользователя с проверкой актуальности.
        """
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        
        if user and user.is_stale():  # Добавить метод is_stale в модель User
            await db.delete(user)
            await db.commit()
            return None
        
        return user

    @staticmethod
    async def cache_user_locally(db: AsyncSession, user_data: UserInDB) -> User:
        """
        Создание/обновление локальной копии пользователя с транзакцией.
        """
        try:
            result = await db.execute(select(User).filter(User.id == user_data.id))
            db_user = result.scalars().first()
            
            if db_user:
                update_data = user_data.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_user, key, value)
                db_user.updated_at = datetime.utcnow()
            else:
                db_user = User(**user_data.dict())
                db.add(db_user)
            
            await db.commit()
            await db.refresh(db_user)
            logger.info(f"Cached user locally: {db_user.id}")
            return db_user
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cache user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cache user data"
            )

    @staticmethod
    async def get_users_by_ids(db: AsyncSession, user_ids: List[int]) -> Dict[int, User]:
        """
        Пакетное получение пользователей с возвратом словаря {id: User}.
        """
        result = await db.execute(select(User).filter(User.id.in_(user_ids)))
        users = result.scalars().all()
        return {user.id: user for user in users}

    @staticmethod
    async def get_or_fetch_user(db: AsyncSession, user_id: int) -> Optional[UserInDB]:
        """
        Комплексное получение пользователя: сначала из локальной БД, 
        затем из внешнего сервиса при необходимости.
        """
        user = await UserService.get_local_user(db, user_id)
        if user:
            return user
        
        user_data = await UserService.get_user_from_auth_service(user_id)
        if user_data:
            return await UserService.cache_user_locally(db, user_data)
        
        return None
