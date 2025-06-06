from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.services.auth.domain.models.user import UserModel


class HashService(ABC):
    @abstractmethod
    def hash_token(self, token: str) -> str: ...
    
    @abstractmethod
    async def verify_password(self, user: UserModel, password: str) -> bool: ...

    @abstractmethod
    async def hash_password(self, password:str) -> str: ...


    
    