import redis
from app.core.config import settings

# Подключение к Redis через URL
cache = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_from_cache(key):
    return cache.get(key)

def set_to_cache(key, value, ttl=300):  # ttl в секундах
    cache.set(key, value, ex=ttl)

def invalidate_cache(key_pattern):
    """
    Удаляет все ключи, соответствующие шаблону.
    Например, invalidate_cache("search_users:*") удалит все ключи, начинающиеся с "search_users:".
    """
    keys = cache.keys(key_pattern)
    if keys:
        cache.delete(*keys)