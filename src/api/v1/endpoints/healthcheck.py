from fastapi import APIRouter, HTTPException, status
import logging

from src.core.dependencies.db_injection import DBDI, db_helper
from src.core.services.tasks.task_health import healthcheck
from src.core.services.database.orm.celery_orm import health_db

router = APIRouter(tags=['api'])
logger = logging.getLogger(__name__)


@router.get('/health')
async def trigger_health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database synchronously
        async with db_helper.async_session() as db_session:
            await health_db(db_session)
        
        # Trigger async component checks
        task = healthcheck.delay()
        
        return {
            'status': 'Health check initiated',
            'database': 'healthy',
            'task_id': str(task.id)
        }
    except Exception as err:
        logger.error(err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database health check failed"
        )
