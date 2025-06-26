from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.user import UserSchema


class UserRepository(ABC):  # Handles ONLY user persistence
    @abstractmethod
    async def create_user(self, session:AsyncSession, user_data:UserSchema) -> Optional[UserModel]: ...
    
    @abstractmethod
    async def delete_user(self, session:AsyncSession, user_id:int) -> None:...

    @abstractmethod
    async def get_user_for_auth(self, session:AsyncSession, login: str) -> UserModel: ...
    
    @abstractmethod
    async def get_user_for_auth_by_id(self, session:AsyncSession, user_id:int) -> UserModel: ...

    @abstractmethod
    async def get_user_for_auth_by_email(self, session:AsyncSession, email:str) ->UserModel: ...
    
    @abstractmethod
    async def create_user(self, user_data: UserSchema) -> UserModel: ...

    @abstractmethod
    async def activate_user(self, session:AsyncSession, user_id: int) -> None: ...

    @abstractmethod
    async def disable_user(self, session:AsyncSession, user_id: int) -> None: ...

    @abstractmethod
    async def update_profile(self, session:AsyncSession, user_id:int, data:dict) -> None: ...
    
    @abstractmethod
    async def change_password_email(self, session:AsyncSession, user:UserModel, new_pass:str, email:str) -> None: ...

    @abstractmethod
    async def give_all_active_users_repo(self, session:AsyncSession) -> Optional[list[UserModel]]: ...