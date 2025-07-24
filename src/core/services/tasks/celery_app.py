import eventlet
eventlet.monkey_patch()  # Must be first import!


import asyncio
from celery.signals import worker_process_init
from celery import Celery

from src.core.config.config import settings

eventlet.monkey_patch()
app = Celery(
    'periodic_tasks',
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
app.conf.worker_pool = 'eventlet'


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
        'schedule': 60.0,
    },
    'disable-inactive-users-hourly': {
        'task': 'src.core.services.tasks.db_tasks.disable_inactive_users_task',
        'schedule': 60.0,
    },
}

@worker_process_init.connect
def setup_worker_event_loop(**kwargs):
    """Create new event loop for each worker process"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except RuntimeError as e:
        if "There is no current event loop" in str(e):
            # This is fine - we're creating the first loop
            pass
        else:
            raise