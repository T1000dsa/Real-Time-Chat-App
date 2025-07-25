import logging
from contextlib import asynccontextmanager
from celery import current_task
from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.celery_app import app
from src.core.services.database.orm.celery_orm import disable_users

logger = logging.getLogger(__name__)


@app.task(bind=True)
def disable_inactive_users_task(self):
    """Synchronous wrapper for async operations with gevent"""
    import asyncio
    
    try:
        # Create new event loop for this greenlet
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async code
        result = loop.run_until_complete(_async_disable_users())
        return {"status": "success", "processed": result}
    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        loop.close()

async def _async_disable_users():
    """Actual async implementation"""
    async with db_helper.async_session() as session:
        await disable_users(session)
        return True