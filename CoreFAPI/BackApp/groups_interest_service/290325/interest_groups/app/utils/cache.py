# app/utils/cache.py
import json
from datetime import timedelta
from functools import wraps
from typing import Callable, Any, Optional, TypeVar
import redis.asyncio as redis
from app.core.config import settings
from app.utils.logger import logger

T = TypeVar('T')

class Cache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def init_cache(self):
        """Инициализация Redis подключения"""
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=0,
            decode_responses=True
        )
        try:
            await self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise

    async def close(self):
        """Закрытие соединения"""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Получение данных из кеша"""
        if not self.redis:
            return None
            
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Сохранение данных в кеш"""
        if not self.redis:
            return
            
        try:
            serialized = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, serialized)
            else:
                await self.redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")

    async def delete(self, key: str):
        """Удаление данных из кеша"""
        if not self.redis:
            return
            
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")

    def cached(self, ttl: Optional[timedelta] = None, key_prefix: str = ""):
        """
        Декоратор для кеширования результатов функций.
        Пример использования:
        @cache.cached(ttl=timedelta(minutes=5), key_prefix="user_data")
        async def get_user(user_id: int): ...
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                if not self.redis:
                    return await func(*args, **kwargs)

                # Генерация ключа кеша
                cache_key = f"{key_prefix}:{args}:{kwargs}"
                
                # Пытаемся получить данные из кеша
                cached_data = await self.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data
                
                # Если нет в кеше, выполняем функцию
                result = await func(*args, **kwargs)
                
                # Сохраняем результат в кеш
                if result is not None:
                    ttl_seconds = int(ttl.total_seconds()) if ttl else None
                    await self.set(cache_key, result, ttl=ttl_seconds)
                
                return result
            return wrapper
        return decorator

# Глобальный экземпляр кеша
cache = Cache()

async def init_cache():
    """Инициализация кеша при старте приложения"""
    await cache.init_cache()

async def close_cache():
    """Закрытие соединения с кешем"""
    await cache.close()