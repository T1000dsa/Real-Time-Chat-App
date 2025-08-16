import logging

from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.taskiq_broker import broker
from src.core.services.database.orm.celery_orm import disable_users

logger = logging.getLogger(__name__)


@broker.task(
    task_name="disable_inactive_users",
    schedule=[{
        "cron": "*/1 * * * *",  # Every minute
        "task_name": "disable_inactive_users",
        "args": [],
        "kwargs": {}
    }]
)
async def disable_inactive_users():
    logger.info("Task started: disable_inactive_users")
    try:
        async with db_helper.async_session() as session:
            result = await disable_users(session)
        logger.info(f"Task completed: {result}")
        return {
            'status': 200, 
            'message': 'Users disabled successfully', 
            'user_counts': result
        }
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        return {'status': 500, 'message': str(e)}