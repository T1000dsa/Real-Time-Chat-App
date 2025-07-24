import logging
import asyncio
from contextlib import asynccontextmanager
from celery import current_task
from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.celery_app import app
from src.core.services.database.orm.celery_orm import disable_users

logger = logging.getLogger(__name__)


@app.task(bind=True)
def disable_inactive_users_task(self):
    """Celery task wrapper with proper async handling"""
    try:
        # Create new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Process users in batches to avoid memory issues
            result = loop.run_until_complete(_process_users_batch())
            return {"status": "success", "processed": result}
        finally:
            # Clean up async resources
            loop.run_until_complete(db_helper.dispose())
            loop.close()
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        return {"status": "error", "message": str(e)}
    
async def _process_users_batch():
    """Process users in a managed session"""
    async with db_helper.async_session() as session:
        await disable_users(session)
        return True