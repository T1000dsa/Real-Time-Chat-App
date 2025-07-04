from celery import Celery
from src.core.config.config import settings

celery = Celery(
    'periodic_tasks',
    broker=f'redis://{settings.redis.host}:{settings.redis.port}/0',
    backend=f'redis://{settings.redis.host}:{settings.redis.port}/0',
    include=[
        'src.core.services.tasks.task_health',
        'src.core.services.tasks.email_task',
        'src.core.services.tasks.db_tasks'
             ]
)

celery.conf.worker_pool = 'celery_pool_asyncio:TaskPool'
celery.conf.worker_concurrency = settings.db.pool_size

# Configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Periodic Tasks
celery.conf.beat_schedule = {
    'healthcheck-every-60-seconds': {
        'task': 'src.core.services.tasks.task_health.healthcheck',
        'schedule': 60.0,
    },

    'db_disable_users': {
        'task': 'src.core.services.tasks.db_tasks.disable_inactive_users_task',
        'schedule': 3600.0, # every hour
    },
}