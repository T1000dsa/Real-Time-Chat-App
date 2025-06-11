from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.services.auth.domain.interfaces.TokenRepository import TokenRepository
from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel
from src.core.services.database.orm.token_crud import (
    select_data_token, 
    insert_data_token,
    revoke_refresh_token
    )
from src.utils.time_check import time_checker


class DatabaseTokenRepository(TokenRepository):
    @time_checker
    async def store_refresh_token(self, user_id: int, token: str) -> None:
        # Stores hashed token in DB (e.g., via SQLAlchemy)
        #await db.execute("INSERT INTO refresh_tokens VALUES (...)")
        pass

    @time_checker
    async def revoke_token(self, session, token: str) -> None:
        await revoke_refresh_token(session, token)
        
    @time_checker
    async def verificate_refresh_token(self, session, token:str) -> Optional[RefreshTokenModel]:
        return await select_data_token(session, token)