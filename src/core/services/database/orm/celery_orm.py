from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
import logging

from src.core.services.auth.domain.models.user import UserModel
from src.core.services.database.orm.token_crud import get_refresh_token_data
from src.utils.time_check import time_checker

logger = logging.getLogger(__name__)

@time_checker
async def disable_users(session: AsyncSession):
    try:
        disabled_count = 0

        users = await session.execute(
            select(UserModel).where(UserModel.is_active == True)
        )
        active_users = users.scalars().all()
        
        now_data = datetime.now()
        logger.debug('active_users')
        for user in active_users:

            refresh_token = await get_refresh_token_data(session, user)
            if refresh_token:
                hours_since_last_activity = (now_data - refresh_token.expires_at).total_seconds() / 3600
                if hours_since_last_activity >= 24:
                    user.is_active = False
                    refresh_token.revoked = True
                    disabled_count+=1
                    await session.commit()
                    
        return disabled_count
    
    except Exception as e:
        logger.error(f"Error in disable_users: {e}")
        raise

@time_checker
async def health_db(session:AsyncSession):
    await session.execute(text('SELECT 1'))