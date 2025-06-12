from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.schemas.auth_schema import RefreshToken
from src.core.services.auth.domain.interfaces.TokenRepository import TokenRepository
from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel
from src.core.services.database.orm.token_crud import (
    select_data_token, 
    update_data_token,
    revoke_refresh_token,
    new_token_insert
    )
from src.utils.time_check import time_checker


class DatabaseTokenRepository(TokenRepository):
    @time_checker
    async def store_new_refresh_token(self, session:AsyncSession, token_schema:RefreshToken):
        await new_token_insert(session, token_schema)

    @time_checker
    async def update_old_refresh_token(self, session:AsyncSession,  token:RefreshToken, old_token:RefreshToken) -> None:
        await update_data_token(session, token, old_token)

    @time_checker
    async def revoke_token(self, session:AsyncSession, token: str) -> None:
        await revoke_refresh_token(session, token)
        
    @time_checker
    async def verificate_refresh_token(self, session:AsyncSession, token:str) -> Optional[RefreshTokenModel]:
        return await select_data_token(session, token)
    
    @time_checker
    async def token_scheme_factory(self, **kwargs) -> RefreshToken:
        return RefreshToken(**kwargs)