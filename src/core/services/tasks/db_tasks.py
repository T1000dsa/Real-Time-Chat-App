import logging
import asyncio
from contextlib import asynccontextmanager
from celery import current_task
from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.celery_app import app
from src.core.services.database.orm.celery_orm import disable_users

logger = logging.getLogger(__name__)


@app.task(bind=True)
async def disable_inactive_users_task(self):
    """Async Celery task to disable inactive users"""
    try:
        async with db_helper.async_session() as session:
            disabled_count = await disable_users(session)
            await session.commit()
            return {
                "status": "success",
                "disabled_count": disabled_count,
                "message": f"Disabled {disabled_count} inactive users"
            }
    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }