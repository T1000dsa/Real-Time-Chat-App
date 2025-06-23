import logging

from src.core.dependencies.db_injection import AsyncSession, db_helper
from src.core.services.tasks.celery import celery
from src.core.config.config import settings

logger = logging.getLogger(__name__)

@celery.task
def healthcheck():
    try:

        logger.info(f'Everything is OK')
        return {
                'status': 200,
                'message': 'Health check successful',
                "run_conf":[settings.run.port, settings.run.host]
            }
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return {
            'status': 500,
            'error': str(e)
        }