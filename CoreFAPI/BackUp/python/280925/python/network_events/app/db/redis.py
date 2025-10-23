import redis.asyncio as Redis
from app.core.config import settings
REDIS_URL = settings.REDIS_URL
redis = Redis.from_url(str(REDIS_URL), decode_responses=True)
