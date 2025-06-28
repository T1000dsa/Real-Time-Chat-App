import logging
import asyncio

from src.core.services.tasks.celery import celery
from src.core.services.cache.redis import manager
from src.core.dependencies.db_injection import db_helper


logger = logging.getLogger(__name__)

async def db_check():
    async with db_helper.async_session() as db_session:
        return db_session

@celery.task
def healthcheck():
    try:
        db_ok = asyncio.run(db_check())
        redis_ok = manager.redis
        celery_ok = celery
        if all([db_ok, redis_ok, celery_ok]):
            logger.info('Health check successful')
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
            raise Exception("Some components are not healthy")
        
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return {
            'status': 500,
            'error': str(e),
            'components': {
                'database': False,
                'redis': False,
                'celery': False
            }
        }