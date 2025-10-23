import redis

# Подключение к Redis
cache = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

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