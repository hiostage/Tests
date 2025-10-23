import aioredis
from app.core.config import settings
REDIS_URL = settings.REDIS_URL
redis = aioredis.from_url(REDIS_URL, decode_responses=True)
