from fastapi import Request, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from src.core.services.auth.token_service import TokenService
from src.core.schemas.auth_schema import RefreshToken
from src.core.services.database.models.user import UserModel
from src.core.schemas.User import UserSchema
from src.core.services.database.orm.user_orm import (
    select_data_user, 
    insert_data, 
    get_all_users, 
    delete_users, 
    select_data_user_id,
    user_activate
    )
from src.core.config.auth_config import (
    credentials_exception,
    ACCESS_TYPE,
    REFRESH_TYPE,
    CSRF_TYPE
)

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, session: AsyncSession, token_service: TokenService):
        self.session = session
        self.token_service = token_service  # Use injected service

    #Not for production, delete later
    async def get_all_users(self) -> list[UserModel]:
        return await get_all_users(self.session)
    
    #Not for production, delete later
    async def delete_all_users(self) -> None:
        return await delete_users(self.session)
    
    async def create_user(self, data: UserSchema) -> None:
        await insert_data(self.session, data)

    async def disable_user(self, user_id:int):
        await user_activate(self.session, user_id, False)

    async def activate_user(self, user_id:int):
        await user_activate(self.session, user_id, True)
    
    async def get_user_by_username(self, username: str, password:str) -> Optional[UserModel]:
        return await select_data_user(self.session, username, password)
    
    async def get_user_by_id(self, user_id:int) -> Optional[UserModel]:
        return await select_data_user_id(self.session, user_id)
    
    async def verify_user_tokens(self, request:Request) -> dict:
        """If evcerything OK return nothing in any else cases raises the exception"""
        
        access_token = request.cookies.get(ACCESS_TYPE)
        refresh_token = request.cookies.get(REFRESH_TYPE)
        csrf_token = request.cookies.get(CSRF_TYPE)

        logger.debug(f"{access_token[-11:]} {refresh_token[-11:]} {csrf_token}")

        for token in (access_token, refresh_token):
            await self.token_service.verify_csrf(token, csrf_token)

        return {
            ACCESS_TYPE:access_token,
            REFRESH_TYPE:refresh_token
        }

    async def gather_user_data(self, request:Request) -> dict:
        user_data =  await self.verify_user_tokens(request=request)
        access_token = await self.token_service.verify_token(user_data[ACCESS_TYPE], ACCESS_TYPE)
        return access_token

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        user = await self.get_user_by_username(username, password)
        if not user:
            return None
        
        await self.activate_user(user.id)
            
        try:
            # Create tokens
            tokens = await self.token_service.create_both_tokens({"sub": str(user.id)})
            
            # Store refresh token
            await self.token_service.store_refresh_token(
                session=self.session,
                user_id=user.id,
                raw_token=tokens[REFRESH_TYPE]
            )
            return tokens
            
        except Exception as err:
            logger.error(f'Authentication failed: {err}')
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication processing failed"
            )
    
    async def logout_user(self, request:Request, response:Response) -> None:

        payload = await self.verify_user_tokens(request=request)
        user_id = int((await self.token_service.verify_token(payload[ACCESS_TYPE], ACCESS_TYPE)).get('sub'))
        refresh_token = payload[REFRESH_TYPE]
        #logger.debug(f"{user_id=} {refresh_token=}")

        try:
            user = await self.get_user_by_id(user_id)
            if user:
                await self.disable_user(user_id)
                #await user.revoke_all_tokens(self.session)
                await self.token_service.revoke_token(session=self.session, token=refresh_token, user_id=user_id)

            for cookie_name in [ACCESS_TYPE, REFRESH_TYPE, CSRF_TYPE]:
                response.delete_cookie(
                    cookie_name,
                    path="/",
                    domain=None,
                    secure=True,
                    httponly=True
                )
            return response
        except Exception as e:
            logger.error(f"Error during token revocation: {e}")
            raise
        
    async def rotate_tokens(self, request:Request):
        return await self.token_service.rotate_tokens(self.session, request)
