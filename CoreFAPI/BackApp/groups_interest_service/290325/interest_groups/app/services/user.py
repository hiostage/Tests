from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, List, Dict
import httpx, datetime
from app.models.user import User
from app.schemas.user import UserBase, UserInDB
from app.core.config import settings
from app.utils.logger import logger
from app.utils.cache import cache  # Предполагаем наличие кеша
from functools import wraps
from datetime import timedelta

class UserService:
    @staticmethod
    @cache(ttl=timedelta(minutes=5), key_prefix="user_data")
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
    def get_local_user(db: Session, user_id: int) -> Optional[User]:
        """
        Получение локальной копии пользователя с проверкой актуальности.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_stale():  # Добавить метод is_stale в модель User
            db.delete(user)
            db.commit()
            return None
        return user

    @staticmethod
    def cache_user_locally(db: Session, user_data: UserInDB) -> User:
        """
        Создание/обновление локальной копии пользователя с транзакцией.
        """
        try:
            db_user = db.query(User).filter(User.id == user_data.id).first()
            
            if db_user:
                # Обновляем только измененные поля
                update_data = user_data.dict(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(db_user, key, value)
                db_user.updated_at = datetime.utcnow()
            else:
                db_user = User(**user_data.dict())
                db.add(db_user)
            
            db.commit()
            db.refresh(db_user)
            logger.info(f"Cached user locally: {db_user.id}")
            return db_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cache user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cache user data"
            )

    @staticmethod
    def get_users_by_ids(db: Session, user_ids: List[int]) -> Dict[int, User]:
        """
        Пакетное получение пользователей с возвратом словаря {id: User}.
        """
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        return {user.id: user for user in users}

    @staticmethod
    async def get_or_fetch_user(db: Session, user_id: int) -> Optional[UserInDB]:
        """
        Комплексное получение пользователя: сначала из локальной БД, 
        затем из внешнего сервиса при необходимости.
        """
        # 1. Проверяем локальную БД
        user = UserService.get_local_user(db, user_id)
        if user:
            return user
            
        # 2. Запрашиваем из внешнего сервиса
        user_data = await UserService.get_user_from_auth_service(user_id)
        if user_data:
            # 3. Кешируем локально
            return UserService.cache_user_locally(db, user_data)
            
        return None