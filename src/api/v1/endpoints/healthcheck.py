from fastapi import APIRouter
import logging

from src.core.dependencies.db_injection import DBDI, db_helper
from src.core.services.tasks.task_health import healthcheck


router = APIRouter(tags=['api'])
logger = logging.getLogger(__name__)


@router.get('/health')
async def trigger_health_check():
    """Endpoint to manually trigger health check"""
    task = healthcheck.delay()
    return {
        'status': 'Health check initiated',
        'task_id': str(task.id)
    }