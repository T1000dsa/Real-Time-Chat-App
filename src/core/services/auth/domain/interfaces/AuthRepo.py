from fastapi import Response
from abc import ABC, abstractmethod

from src.core.services.auth.domain.models.user import UserModel


class AuthRepository(ABC):  # Handles ONLY authentication
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> UserModel: ...
    
    @abstractmethod
    async def logout(self, response: Response) -> Response: ...