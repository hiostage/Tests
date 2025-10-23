import os
import logging
from urllib.parse import urlparse
from typing import Optional
import redis.asyncio as redis  # Используем асинхронный клиент
from app.core.config import settings

# Настройка логирования
logging.basicConfig()
logger = logging.getLogger(__name__)

class RedisConnectionError(Exception):
    """Ошибка соединения с Redis"""
    pass

def validate_redis_url(url: str) -> bool:
    """Проверяет валидность Redis URL"""
    parsed = urlparse(url)
    return parsed.scheme in {"redis", "rediss"}  # Поддержка SSL

async def check_connection(redis_client: redis.Redis) -> bool:
    """Асинхронно проверяет соединение с Redis"""
    try:
        return await redis_client.ping()
    except redis.RedisError as e:
        logger.error(f"Redis connection failed: {e}")
        return False

async def get_redis() -> redis.Redis:
    """Возвращает клиент Redis с проверкой соединения"""
    redis_url = settings.REDIS_url #os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    if not validate_redis_url(redis_url):
        raise ValueError("Invalid Redis URL")

    if os.getenv("TESTING"):
        redis_url = "redis://localhost:6379/1"  # Отдельная база для тестов

    redis_client = redis.Redis.from_url(
        redis_url,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        decode_responses=True,
        health_check_interval=30
    )

    if not await check_connection(redis_client):
        raise RedisConnectionError("Could not connect to Redis")

    return redis_client
