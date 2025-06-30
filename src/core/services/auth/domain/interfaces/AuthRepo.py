from fastapi import Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod
from typing import Optional

from src.core.schemas.user import UserSchema
from src.core.services.auth.domain.models.user import UserModel


class AuthRepository(ABC):  # Handles ONLY authentication
    @abstractmethod
    async def authenticate_user(self, login: str, password: str) -> dict: ...
    
    @abstractmethod
    async def logout(self, request:Request, response: Response) -> Response: ...

    @abstractmethod
    async def register_user(self, user_data:UserSchema) -> None: ...

    @abstractmethod
    async def set_cookies(self, response:Response, tokens:dict) -> Response: ...

    @abstractmethod
    async def token_rotate(self, request) -> Optional[dict]: ...