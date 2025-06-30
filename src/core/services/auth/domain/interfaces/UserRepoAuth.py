from fastapi import Request
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.services.auth.domain.models.user import UserModel


class UserRepoAuth(ABC):
    @abstractmethod
    async def update_profile_user(self, user_id:int,data:dict) -> None: ...

    @abstractmethod
    async def password_change(self, user:UserModel, new_pass:str, email:str): ...
    
    @abstractmethod
    async def get_all_active_users(self, session:AsyncSession): ...

    @abstractmethod
    async def is_active(self, session:AsyncSession, request:Request): ...

    @abstractmethod
    async def gather_user_data(self, session:AsyncSession, request:Request) -> UserModel: ...