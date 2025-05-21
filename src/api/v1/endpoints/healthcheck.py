from fastapi import APIRouter
import logging

from src.core.dependencies.db_injection import DBDI


router = APIRouter(tags=['api'])
logger = logging.getLogger(__name__)

@router.get('/health')
async def check(db:DBDI):
    logger.info(f'{db.is_active=}')
    logger.info('Everything is fine')
    return 'pong'