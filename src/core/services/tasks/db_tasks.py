import logging
import asyncio

from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.celery import celery
from src.core.services.database.orm.celery_orm import disable_users


logger = logging.getLogger(__name__)

async def disable_inactive_users_async():
    try:
        async with db_helper.async_session() as db_session:
            await disable_users(db_session)
            logger.info("Successfully disabled users!")
            return {
                "status": "success"
            }
    except Exception as e:
        logger.error(f"Error disabling inactive users: {e}")
        return {
                "status": "bad_result"
            }
    

@celery.task
def disable_inactive_users_task():
    asyncio.run(disable_inactive_users_async())
    return {
                "status": "success"
            }