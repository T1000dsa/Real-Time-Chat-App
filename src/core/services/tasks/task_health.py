import logging
import redis
from sqlalchemy import text

from src.core.services.tasks.celery_app import app
from src.core.dependencies.db_injection import db_helper

logger = logging.getLogger(__name__)

@app.task(bind=True)
def healthcheck(self):
    """Eventlet-compatible health check"""
    try:
        # Import eventlet's patched versions
        from eventlet import sleep
        from eventlet.asyncio import asyncio
        
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Check database connection
        async def db_check():
            try:
                async with db_helper.async_session() as session:
                    await session.execute(text("SELECT 1"))
                return True
            except Exception as err:
                logger.error(err)
                return False
        
        # Check Redis connection
        def redis_check():
            try:
                r = redis.Redis(host='redis', port=6379)
                return r.ping()
            except Exception:
                return False
        
        db_status = loop.run_until_complete(db_check())
        redis_status = redis_check()
        
        if db_status and redis_status:
            return {
                'status': 200,
                'message': 'Health check successful',
                'components': {
                    'database': True,
                    'redis': True,
                    'celery': True
                }
            }
        else:
            return {
                'status': 500,
                'message': 'Health check failed',
                'components': {
                    'database': db_status,
                    'redis': redis_status,
                    'celery': True
                }
            }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            'status': 500,
            'error': str(e),
            'components': {
                'database': False,
                'redis': False,
                'celery': False
            }
        }