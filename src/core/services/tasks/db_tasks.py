import logging
from asgiref.sync import async_to_sync


from src.core.dependencies.db_injection import db_helper
from src.core.services.tasks.celery_app import app
from src.core.services.database.orm.celery_orm import disable_users


logger = logging.getLogger(__name__)


@app.task
async def disable_inactive_users_task():
    """Native async Celery task"""
    try:
        async with db_helper.async_session() as session:
            await disable_users(session)
        return {'status': 200, 'message': 'Users disabled successfully'}
    except Exception as e:
        return {'status': 500, 'message': str(e)}