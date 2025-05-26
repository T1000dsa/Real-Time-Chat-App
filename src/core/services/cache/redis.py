import redis.asyncio as redis
from src.core.config.config import settings

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.redis = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db
        )
        self.pubsub = self.redis.pubsub()

    async def subscribe(self, channel: str):
        await self.pubsub.subscribe(channel)
        return self.pubsub

    async def publish(self, channel: str, message: str):
        await self.redis.publish(channel, message)