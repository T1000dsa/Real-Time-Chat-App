from abc import ABC, abstractmethod
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.schemas.auth_schema import RefreshToken


class TokenRepository(ABC):
    @abstractmethod
    async def store_new_refresh_token(self, session:AsyncSession, token_schema:RefreshToken): ...

    @abstractmethod
    async def update_old_refresh_token(self, session:AsyncSession,  token:RefreshToken, old_token:RefreshToken) -> None: ...

    @abstractmethod
    async def revoke_token(self, session:AsyncSession, token: str) -> None: ...

    @abstractmethod
    async def verificate_refresh_token(self, session:AsyncSession, token:str) -> Optional[RefreshTokenModel]: ...
    
    @abstractmethod
    async def token_scheme_factory(self, **kwargs) -> RefreshToken: ...

    @abstractmethod
    async def refresh_token_flow(
        self, 
        request:Request,
        session: AsyncSession,
        jwt_service:JWTService
        ): ...
    
    @abstractmethod
    async def save_message_db(self, session:AsyncSession, message:str, room_id:str, sender_id:str): ...

    @abstractmethod
    async def receive_messages(self, session:AsyncSession, room_id:str, sender_id:str): ...