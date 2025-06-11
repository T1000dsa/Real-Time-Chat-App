from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.user import UserSchema
from src.core.services.auth.domain.interfaces import UserRepository
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.core.services.database.orm.user_orm import (
    select_data_user, 
    select_data_user_id, 
    select_user_email, 
    insert_data_user, 
    delete_data_user, 
    update_data_user,
    user_activate,
    update_profile_file, 
    update_password_by_email
    )
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)

class UserService(UserRepository):
    def __init__(self, session: AsyncSession, hash_service: Bcryptprovider):
        self.session = session
        self._hash = hash_service

    @time_checker
    async def get_user_for_auth(self, login: str) -> UserModel:
        return await select_data_user(self.session, login)
    
    @time_checker
    async def get_user_for_auth_by_id(self, user_id:int):
        return await select_data_user_id(self.session, user_id)
    
    @time_checker
    async def get_user_for_auth_by_email(self, email:str):
        return await select_user_email(self.session, email)
    
    @time_checker
    async def create_user(self, user_data:UserSchema) -> Optional[UserModel]:
        user = await insert_data_user(self.session, user_data, self._hash)
        return user
    
    @time_checker
    async def delete_user(self, user_id:int):
        await delete_data_user(self.session, user_id)

    @time_checker
    async def activate_user(self, user_id: int) -> None:
        await user_activate(self.session, user_id, True)

    @time_checker
    async def disable_user(self, user_id: int) -> None:
        await user_activate(self.session, user_id, False)
        
    @time_checker
    async def update_profile(self, user_id:int, data:dict):
        user = await select_data_user_id(self.session, user_id)
        await update_profile_file(self.session, user, data)

    @time_checker
    async def change_password_email(self, email:str, new_pass:str) -> None:
        user = select_user_email(self.session, email)
        try:
            if user:
                await update_password_by_email(self.session, user, new_pass)
        except Exception as err:
            logger.error(err)

        