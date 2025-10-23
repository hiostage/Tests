from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Request, status
from typing import Optional, List, Dict
import httpx
from app.models.user import User
from app.schemas.user import UserBase, UserInDB
from app.core.config import settings
from app.utils.logger import logger
from app.utils.cache import cache
from datetime import datetime, timedelta
from sqlalchemy.future import select

class UserService:
    @staticmethod
    async def get_current_user_from_session(request: Request) -> Optional[UserInDB]:
        """
        Получает текущего пользователя из сессии через auth-proxy
        Args:
            request: FastAPI Request объект для доступа к cookies
        Returns:
            UserInDB если сессия валидна, иначе None
        """
        session_id = request.cookies.get("session_id")
        if not session_id:
            logger.debug("No session_id in cookies")
            return None

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                response = await client.get(
                    f"{settings.AUTH_PROXY_URL}check_session",
                    cookies={"session_id": session_id},
                    headers={"X-Real-IP": request.client.host} if request.client else None
                )

                # Логируем полученный статус и содержимое ответа
                logger.debug(f"Auth service response: {response.status_code} - {response.text}")

                if response.status_code == 200:
                    user_data = response.json()

                    if "user_id" in user_data and user_data["user_id"]:
                        logger.debug(f"Authenticated user: {user_data['user_id']}")

                        # Дополнительная проверка на поля
                        if "username" not in user_data or not user_data["username"]:
                            logger.warning("Username missing in response from auth service")
                            return None

                        return UserInDB(
                            id=user_data["user_id"],
                            username=user_data["username"],
                            email=user_data.get("email"),
                            is_active=user_data.get("is_active", True),
                            permissions=user_data.get("permissions", [])
                        )
                    else:
                        logger.warning(f"Invalid user data from auth service: {user_data}")
                else:
                    logger.warning(f"Invalid session: {response.status_code} - {response.text}")

        except httpx.TimeoutException:
            logger.error("Auth service timeout")
        except httpx.RequestError as e:
            logger.error(f"Request error while contacting auth service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")

        return None


    @staticmethod
    @cache.cached(ttl=timedelta(minutes=5), key_prefix="user_data")
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

    @staticmethod
    async def get_local_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Получает пользователя из локальной БД с проверкой актуальности
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if user and (datetime.utcnow() - user.updated_at) > timedelta(days=1):
            await db.delete(user)
            await db.commit()
            return None
            
        return user

    @staticmethod
    async def cache_user_locally(db: AsyncSession, user_data: UserInDB) -> User:
        """
        Кеширует/обновляет данные пользователя в локальной БД
        """
        try:
            user = await db.get(User, user_data.id)
            if user:
                for field, value in user_data.dict(exclude_unset=True).items():
                    setattr(user, field, value)
            else:
                user = User(**user_data.dict())
                db.add(user)
            
            user.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cache user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User data caching failed"
            )

    @staticmethod
    async def get_or_fetch_user(
        db: AsyncSession, 
        request: Request, 
        user_id: Optional[int] = None
    ) -> Optional[UserInDB]:
        """
        Основной метод для получения пользователя:
        1. Пытается получить из сессии
        2. Если не найдено - из локальной БД
        3. Если не найдено - из внешнего сервиса
        """
        # Сначала пробуем получить из сессии
        session_user = await UserService.get_current_user_from_session(request)
        if session_user:
            if user_id and session_user.id != user_id:
                logger.warning(f"Session user {session_user.id} != requested {user_id}")
                return None
            return await UserService.cache_user_locally(db, session_user)
        
        # Fallback для случаев, когда запрашивают конкретного пользователя
        if user_id:
            local_user = await UserService.get_local_user(db, user_id)
            if local_user:
                return local_user
                
            external_user = await UserService.get_current_user_from_session(request)
            if external_user:
                return await UserService.cache_user_locally(db, external_user)
        
        return None

    @staticmethod
    async def get_users_by_ids(
        db: AsyncSession, 
        user_ids: List[int]
    ) -> Dict[int, User]:
        """
        Пакетное получение пользователей
        """
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        return {user.id: user for user in result.scalars().all()}
    
    @staticmethod
    async def get_user_id_from_session(request: Request) -> Optional[int]:
        user = await UserService.get_current_user_from_session(request)
        return user.id if user else None
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        """
        Получение пользователя по его ID.
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()  # Возвращаем первого найденного пользователя или None

