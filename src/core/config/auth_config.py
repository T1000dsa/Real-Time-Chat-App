from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.core.config.config import settings
from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.User import UserSchema
from src.core.services.auth.infrastructure import Bcryptprovider, UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthCore:
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.REFRESH_TOKEN_EXPIRE = timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)
        
        self.ACCESS_TYPE = 'access'
        self.REFRESH_TYPE = 'refresh'

class AuthService(AuthCore):
    def __init__(self, session: AsyncSession,user_repo: UserService, hash_service: Bcryptprovider):
        self.session = session
        self._repo = user_repo
        self._hash = hash_service
    
    async def get_user_for_auth(self, username: str) -> UserModel:
        return await self._repo.get_user_for_auth(username)
    
    async def get_user_for_auth_by_id(self, user_id:int):
        return await self._repo.get_user_for_auth_by_id(self.session, user_id)
    
    async def get_user_for_auth_by_email(self, email:str):
        return await self._repo.get_user_for_auth_by_id(self.session, email)

    async def create_user(self, user_data:UserSchema) -> Optional[UserModel]:
        user = await self._repo.create_user(self.session, user_data, self._hash)
        return user
    
    async def delete_user(self, user_id:int):
        await self._repo.delete_user(self.session, user_id)