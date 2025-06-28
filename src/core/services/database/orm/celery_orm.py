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
async def disable_users(session:AsyncSession):
    users = select(UserModel)
    all_users = (await session.execute(users)).scalars().all()
    now_data = datetime.now()
    logger.debug(all_users)
    for item in all_users:
        if item.is_active:
            res = await get_refresh_token_data(session, item)
            if res:
                if int((now_data - res.expires_at).seconds/3600) >= 6:
                    item.is_active = False
                    res.revoked = True
                    await session.commit()
                    await session.refresh(item)

@time_checker
async def health_db(session:AsyncSession):
    await session.execute(text('SELECT 1'))