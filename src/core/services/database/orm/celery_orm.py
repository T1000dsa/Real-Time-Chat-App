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
        if item.is_active:
            res = await get_refresh_token_data(session, item)
            if res:
                if int((now_data - res.expires_at).seconds/3600) >= 6:
                    item.is_active = False
                    res.revoked = True
                    await session.commit()
                    await session.refresh(item)