from backend.core.redis_client import redis

# Agent to Agent communication
async def publish(channel, message):
    await redis.publish(channel, message)

async def subscribe(channel):
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    async for msg in pubsub.listen():
        if msg['type'] == 'message':
            yield msg['data']