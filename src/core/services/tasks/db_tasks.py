import logging
from eventlet.asyncio import asyncio

from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.celery_app import app
from src.core.services.database.orm.celery_orm import disable_users

logger = logging.getLogger(__name__)

@app.task(bind=True)
def disable_inactive_users_task(self):
    """Eventlet-compatible task that works with async code"""
    try:
        # Import eventlet's patched versions
        from eventlet import sleep
        
        
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function
        result = loop.run_until_complete(_disable_inactive_users())
        logger.debug(result)
        return result
    except Exception as err:
        logger.error(f"Error in disable_inactive_users_task: {str(err)}")
        return {'status': 500, 'message': str(err)}
    finally:
        try:
            if loop and not loop.is_closed():
                loop.close()
        except:
            pass

async def _disable_inactive_users():
    """Actual async database operation"""
    try:
        async with db_helper.async_session() as session:
            result = await disable_users(session)
        return {
            'status': 200, 
            'message': 'Users disabled successfully', 
            'user_counts': result
        }
    except Exception as e:
        logger.error(f"Error in _disable_inactive_users: {str(e)}")
        return {'status': 500, 'message': str(e)}