import aioredis
from backend.config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


# Agent to Agent communication
async def publish(channel, message):
    await redis.publish(channel, message)

async def subscribe(channel):
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    async for msg in pubsub.listen():
        if msg['type'] == 'message':
            yield msg['data']