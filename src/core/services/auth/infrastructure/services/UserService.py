from fastapi import Request
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.services.auth.domain.models.user import UserModel
from src.core.services.auth.domain.interfaces.UserRepoAuth import UserRepoAuth
from src.core.services.auth.infrastructure.services.User_Crud import UserService
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)

class UserServiceAuth(UserRepoAuth):
    def __init__(
            self, 
            user_repo: UserService, 
            token_service:JWTService,
            ):
        self._repo = user_repo
        self._token = token_service
        
    @time_checker
    async def update_profile_user(self, session:AsyncSession, user_id:int,data:dict) -> None:
        await self._repo.update_profile(session, user_id, data)

    @time_checker
    async def password_change(self, session:AsyncSession, user:UserModel, new_pass:str, email:str):
        await self._repo.change_password_email(session, user, new_pass, email)

    @time_checker
    async def get_all_active_users(self, session:AsyncSession):
        return await self._repo.give_all_active_users_repo(session)
    
    @time_checker
    async def is_active(self, session:AsyncSession, request:Request):
        user_data = await self.gather_user_data(session, request)
        return user_data.is_active
    
    @time_checker
    async def gather_user_data(self, session:AsyncSession, request:Request) -> UserModel:
        try:
            verified_token = await self._token.verify_token(request, self._token.ACCESS_TYPE)
            sub = int(verified_token.get('sub'))
            return await self._repo.get_user_for_auth_by_id(session, sub)
        
        except ExpiredSignatureError as err:
            logger.info(f'Handled {err}')
            verified_token = await self._token.verify_token_unsafe(request, self._token.ACCESS_TYPE)
            sub = int(verified_token.get('sub'))
            return await self._repo.get_user_for_auth_by_id(session, sub)
        except Exception as err:
            logger.critical(err)
            raise err