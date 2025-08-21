import logging
import asyncio

from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from taskiq.schedule_sources import LabelScheduleSource
from taskiq import TaskiqScheduler

from src.core.config.config import settings

logger = logging.getLogger(__name__)


result_backend = RedisAsyncResultBackend(
    redis_url=f"redis://{settings.redis.host}:{settings.redis.port}/1",
)

# Or you can use PubSubBroker if you need broadcasting
# Or ListQueueBroker if you don't want acknowledges
broker = RedisStreamBroker(
    url=f"redis://{settings.redis.host}:{settings.redis.port}/1",
).with_result_backend(result_backend)


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)