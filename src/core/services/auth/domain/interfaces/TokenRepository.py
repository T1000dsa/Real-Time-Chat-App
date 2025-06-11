from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel


class TokenRepository(ABC):
    @abstractmethod
    async def store_refresh_token(
        self,
        session: AsyncSession,
        user_id: int,
        raw_token: str,
        previous_token_id: Optional[int] = None
    ) -> None: ...

    @abstractmethod
    async def revoke_token(self, session, token: str) -> None: ...

    async def verificate_refresh_token(self, session, token:str) -> Optional[RefreshTokenModel]: ...