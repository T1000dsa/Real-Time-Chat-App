from celery import Celery
from datetime import timedelta

from src.core.config.config import settings


app = Celery(
    __name__,
    broker=f'redis://{settings.redis.host}:{settings.redis.port}/0',
    backend=f'redis://{settings.redis.host}:{settings.redis.port}/0',
    include=[
        'src.core.services.tasks.task_health',
        'src.core.services.tasks.email_task',
        'src.core.services.tasks.db_tasks'
    ]
)
 

# Async configuration
app.conf.worker_concurrency = 4
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_pool = 'asyncio'  


# Task configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
)

# Periodic Tasks
app.conf.beat_schedule = {
    'healthcheck-every-60-seconds': {
        'task': 'src.core.services.tasks.task_health.healthcheck',
        'schedule': timedelta(minutes=1),
    },
    'disable-inactive-users-hourly': {
        'task': 'src.core.services.tasks.db_tasks.disable_inactive_users_task',
        'schedule': timedelta(minutes=1),
    },
}