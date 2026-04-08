import redis.asyncio as aioredis
from backend.config import REDIS_URL

redis = aioredis.from_url(REDIS_URL)