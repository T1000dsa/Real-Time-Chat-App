from fastapi import Response
from abc import ABC, abstractmethod
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

class TokenService(ABC):
    @abstractmethod
    async def create_token(self, data:dict, expires_delta:timedelta, token_type:str): ...

    @abstractmethod
    async def verify_token(self, token: str, token_type: str) -> dict: ...

    @abstractmethod
    async def rotate_tokens(
        self, 
        session: AsyncSession,
        refresh_token: str
    ) -> dict: ...
    
    @abstractmethod
    async def set_secure_cookies(
        self,
        response: Response,
        tokens:dict
    ) -> Response: ...

    async def clear_tokens(self, response: Response) -> Response: ...