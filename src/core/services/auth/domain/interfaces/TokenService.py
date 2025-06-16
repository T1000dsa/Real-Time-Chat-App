from fastapi import Response, Request
from abc import ABC, abstractmethod
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession


class TokenService(ABC):
    @abstractmethod
    async def create_token(self, data:dict, expires_delta:timedelta, token_type:str): ...

    @abstractmethod
    async def create_tokens(self, data:dict) -> dict: ...

    @abstractmethod
    async def verify_token(self, request:Request, token_type:str) -> dict: ...

    @abstractmethod 
    async def verify_token_unsafe(self, request: Request, token_type: str) -> dict: ...

    @abstractmethod
    async def rotate_tokens(
        self, 
        request:Request,
        session: AsyncSession,
        refresh_token: str, 
        token_repo
    ) -> dict: ...
    
    @abstractmethod
    async def set_secure_cookies(
        self,
        response: Response,
        tokens:dict
    ) -> Response: ...

    @abstractmethod
    async def clear_tokens(self, response: Response) -> Response: ...
    
    @abstractmethod
    async def verify_websocket_token(self, token: str, token_type: str) -> dict: ...