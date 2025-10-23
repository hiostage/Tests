# app/utils/cache.py
import json
from datetime import timedelta
from functools import wraps
from typing import Callable, Any, Optional, TypeVar, Awaitable
import redis.asyncio as redis
from app.core.config import settings
from app.utils.logger import logger
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

T = TypeVar('T')

class Cache:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def init_cache(self):
        """Инициализация Redis подключения"""
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
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
            # Если это Pydantic модель (для Pydantic v2)
            if hasattr(value, "model_dump"):
                value = value.model_dump()  # Используем model_dump() для Pydantic v2
            elif hasattr(value, "__dict__"):  # Для SQLAlchemy или других объектов
                value = vars(value)  # Преобразуем в словарь

            # Сериализуем в JSON
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
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                if not self.redis:
                    return await func(*args, **kwargs)

                cache_key = f"{key_prefix}:{args}:{kwargs}"

                cached_data = await self.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data

                result = await func(*args, **kwargs)  # Дожидаемся выполнения
                if result is not None:
                    if ttl is not None:
                        # Если ttl — это объект timedelta, то вызываем total_seconds()
                        ttl_seconds = int(ttl.total_seconds()) if isinstance(ttl, timedelta) else ttl
                    else:
                        ttl_seconds = None
                    await self.set(cache_key, result, ttl=ttl_seconds)

                return result
            return wrapper
        return decorator


# Глобальный экземпляр кеша
cache = Cache()

async def init_cache():
    """Инициализация кеша при старте приложения"""
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )

    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    
    await cache.init_cache()
    logger.info("Cache initialized successfully")

async def close_cache():
    """Закрытие соединения с кешем"""
    await cache.close()
    logger.info("Cache connection closed")