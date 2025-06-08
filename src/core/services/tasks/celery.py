from celery import Celery
from src.core.config.config import settings

app = Celery(
    'periodic_tasks',
    broker=f'redis://{settings.redis.host}:{settings.redis.port}/0',
    backend=f'redis://{settings.redis.host}:{settings.redis.port}/0',
    include=['src.core.services.tasks.task_health']
)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Periodic Tasks
app.conf.beat_schedule = {
    'healthcheck-every-10-seconds': {
        'task': 'src.core.services.tasks.task_health.healthcheck',
        'schedule': 10.0,
    },
}