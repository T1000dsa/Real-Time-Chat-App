from abc import ABC, abstractmethod

from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.User import UserSchema


class UserRepository(ABC):  # Handles ONLY user persistence
    @abstractmethod
    async def create_user(self, username: str, password:str) -> UserModel: ...
    
    @abstractmethod
    async def delete_user(self, user_id:int)-> None: ...

    @abstractmethod
    async def get_user_for_auth(self, username: str) -> UserModel: ...
    
    @abstractmethod
    async def get_user_for_auth_by_id(self, user_id:int) -> UserModel: ...

    @abstractmethod
    async def get_user_for_auth_by_email(self, enail: str) -> UserModel: ...
    
    @abstractmethod
    async def create_user(self, user_data: UserSchema) -> UserModel: ...

    @abstractmethod
    async def activate_user(self, user_id: int) -> None: ...

    @abstractmethod
    async def disable_user(self, user_id: int) -> None: ...