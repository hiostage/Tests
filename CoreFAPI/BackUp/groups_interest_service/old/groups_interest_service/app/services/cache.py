from redis import Redis
from app.config.settings import settings
import json

redis = Redis.from_url(settings.REDIS_URL)

def cache_popular_groups(groups: list, expire: int = 3600):
    """Кэширует топ-10 групп в Redis"""
    redis.setex("popular_groups", expire, json.dumps(groups))

def get_cached_popular_groups() -> list | None:
    """Получает закэшированные группы"""
    cached = redis.get("popular_groups")
    return json.loads(cached) if cached else None