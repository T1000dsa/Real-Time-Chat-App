from fastapi import Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from jose.exceptions import ExpiredSignatureError
from datetime import datetime, timezone
import uuid
import logging

from src.core.schemas.user import UserSchema
from src.core.services.auth.domain.models.user import UserModel
from src.core.services.auth.domain.interfaces import AuthRepository
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.services.auth.infrastructure.services.User_Crud import UserService
from src.core.services.auth.infrastructure.repositories.DatabaseTokenRepository import DatabaseTokenRepository
from src.core.exceptions.auth_exception import credentials_exception, inactive_user_exception
from src.utils.time_check import time_checker
from src.core.config.config import main_prefix

logger = logging.getLogger(__name__)


class AuthProvider(AuthRepository):
    def __init__(
            self, 
            session:AsyncSession,
            user_repo: UserService, 
            hash_service: Bcryptprovider, 
            token_service:JWTService, 
            db_repo:DatabaseTokenRepository
            ):
        
        self.session = session
        self._repo = user_repo
        self._hash = hash_service
        self._token = token_service
        self._db = db_repo

    @time_checker
    async def authenticate_user(self, login, password) -> dict:
        """
        Three-step authentication. 
        1. we search users in db, if we find them, return back to authenticate_user UserModel.
        2. we verify input password and actual hashed password that stored in database. 
        3. if everything is okay gain tokens.
        4. store tokens.
        5. send back tokens.
        """
        logger.debug(f'{login} tries to authorize...')
        # Fisrt step
        user:UserModel = await self._repo.get_user_for_auth(self.session, login)
        if not user:
            #raise KeyError('user not found') # Temporary. Raise with expept factory, not from credential 
            logger.debug("User wasn't find by login")
            raise credentials_exception
        logger.debug(f'{user.login} verificated')
        
        # Second step
        res = await self._hash.verify_password(password, user.password)
        if not res:
            #raise KeyError('username or password not matched') # actually username(login) is matched, just making vague response for security
            logger.debug("User password is invalid")
            return credentials_exception
        logger.debug(f'{user.login} password is correct')
        
        # Third step 
        # gain_tokens
        user_data = {'sub':str(user.id)}
        tokens = await self._token.create_tokens(user_data)
        logger.debug(f'tokens created successfully')

        # activate user
        await self._repo.activate_user(self.session, user.id)
        logger.debug(f'User {user.login} activated')

        # Fourth step
        refresh_token = tokens.get(self._token.REFRESH_TYPE)
        date = (datetime.now(timezone.utc)+self._token.REFRESH_TOKEN_EXPIRE)
        family_id = str(uuid.uuid4())

        token_schema = await self._db.token_scheme_factory(
            user_id=user.id,
            token=refresh_token,
            expires_at=date,
            revoked=False,
            replaced_by_token=None,
            family_id=family_id,
            previous_token_id=None,
            device_info=None
        )
        await self._db.store_new_refresh_token(self.session, token_schema)

        # Fifth step
        return tokens
    
    @time_checker
    async def register_user(self, user_data:UserSchema) -> None:
        await self._repo.create_user(self.session, user_data)

    @time_checker
    async def gather_user_data(self, request:Request) -> UserModel:
        try:
            verified_token = await self._token.verify_token(request, self._token.ACCESS_TYPE)
            sub = int(verified_token.get('sub'))
            return await self._repo.get_user_for_auth_by_id(self.session, sub)
        
        except ExpiredSignatureError as err:
            logger.info(f'Handled {err}')
            verified_token = await self._token.verify_token_unsafe(request, self._token.ACCESS_TYPE)
            sub = int(verified_token.get('sub'))
            return await self._repo.get_user_for_auth_by_id(self.session, sub)
        except Exception as err:
            logger.critical(err)
            raise err

    @time_checker
    async def set_cookies(self, response:Response, tokens:dict) -> Response:
        settle = await self._token.set_secure_cookies(response, tokens)
        return settle
    
    @time_checker
    async def token_rotate(self, request) -> Optional[dict]:
        return await self._token.rotate_tokens(request, self.session, self._db)

    
    @time_checker
    async def logout(self, request:Request) -> Response:
        response = RedirectResponse(url=f'{main_prefix}/login', status_code=302)
        # gain token from request cookie
        unverified_token_access = await self._token.verify_token_unsafe(request, self._token.ACCESS_TYPE)
        sub = int(unverified_token_access.get('sub'))
        token_refresh = request.cookies.get(self._token.REFRESH_TYPE)
        user = await self._repo.get_user_for_auth_by_id(self.session, sub)
        logger.debug(f"User {user.login} tries to logout")

        # disable user
        await self._repo.disable_user(self.session, sub)

        # revoke token
        await self._db.revoke_token(self.session, token_refresh)

        # Return response with cleaned cookies
        return await self._token.clear_tokens(response)
    
    @time_checker
    async def update_profile_user(self, user_id:int,data:dict) -> None:
        await self._repo.update_profile(self.session, user_id, data)
    
    @time_checker
    async def password_change(self, email:str, new_password:str):
        await self._repo.change_password_email(self.session, email, new_password)
