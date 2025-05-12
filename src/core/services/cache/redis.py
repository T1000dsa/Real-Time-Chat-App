import redis.asyncio as redis
from src.core.config.config import settings

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.redis = redis.Redis(
            host=settings.redis_settings.host,
            port=settings.redis_settings.port,
            db=settings.redis_settings.db
        )
        self.pubsub = self.redis.pubsub()

    async def subscribe(self, channel: str):
        await self.pubsub.subscribe(channel)
        return self.pubsub

    async def publish(self, channel: str, message: str):
        await self.redis.publish(channel, message)