from fastapi import Response, Request
from abc import ABC, abstractmethod

from src.core.schemas.user import UserSchema
from src.core.services.auth.domain.models.user import UserModel


class AuthRepository(ABC):  # Handles ONLY authentication
    @abstractmethod
    async def authenticate_user(self, login: str, password: str) -> dict: ...
    
    @abstractmethod
    async def logout(self, request:Request, response: Response) -> Response: ...

    @abstractmethod
    async def register_user(self, user_data:UserSchema) -> None:
        pass

    @abstractmethod
    async def gather_user_data(self, request:Request) -> UserModel: ...

    async def set_cookies(self, response:Response, tokens:dict) -> Response: ...