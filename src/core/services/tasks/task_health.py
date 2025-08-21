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

        def redis_check():
            try:
                r = redis.Redis(host='redis', port=6379)
                return r.ping()
            except Exception:
                return False
        
        redis_status = redis_check()
        
        return {
                'status': 500,
                'message': 'Health check failed',
                'components': {
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