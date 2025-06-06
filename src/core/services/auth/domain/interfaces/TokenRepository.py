from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

class TokenRepository(ABC):
    @abstractmethod
    async def is_token_revoked(self, session: AsyncSession, token: str) -> bool: ...

    @abstractmethod
    async def store_refresh_token(
        self,
        session: AsyncSession,
        user_id: int,
        raw_token: str,
        previous_token_id: Optional[int] = None
    ) -> None: ...

    @abstractmethod
    async def revoke_token(self, session: AsyncSession, token:str): ...