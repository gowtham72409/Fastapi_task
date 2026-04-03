import redis.asyncio as aioredis
from backend.config import REDIS_URL

redis = aioredis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=20,          
    socket_connect_timeout=2,   
    socket_timeout=2,            
    retry_on_timeout=True,      
)