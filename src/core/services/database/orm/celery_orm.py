from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from src.core.services.auth.domain.models.user import UserModel
from src.core.services.database.orm.token_crud import get_refresh_token_data

logger = logging.getLogger(__name__)


async def disable_users(session:AsyncSession):
    users = select(UserModel)
    all_users = (await session.execute(users)).scalars().all()
    now_data = datetime.now()
    logger.debug(all_users)
    for item in all_users:
        res = await get_refresh_token_data(session, item)
        if res:
            if (now_data - res.expires_at).days >= 1:
                item.is_active = False
                await session.commit()
                await session.refresh(item)