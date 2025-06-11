from fastapi import Response, Request
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

logger = logging.getLogger(__name__)


class AuthProvider(AuthRepository):
    def __init__(self, user_repo: UserService, hash_service: Bcryptprovider, token_service:JWTService, db_repo:DatabaseTokenRepository):
        self._repo = user_repo
        self._hash = hash_service
        self._token = token_service
        self._db = db_repo

    @time_checker
    async def authenticate_user(self, login, password) -> dict:
        """
        Three-step authentication. 
        Firstly we search users in db, if we find them, return back to authenticate_user UserModel.
        Secondly we verify input password and actual hashed password that stored in database. 
        Thirdly if everything is okay gain tokens and sent them back toward login logic.
        """
        logger.debug(f'{login} tries to authorize...')
        # Fisrt step
        user:UserModel = await self._repo.get_user_for_auth(login)
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
        await self._repo.activate_user(user.id)
        logger.debug(f'User {user.login} activated')
        return tokens
    
    @time_checker
    async def register_user(self, user_data:UserSchema) -> None:
        await self._repo.create_user(user_data)

    @time_checker
    async def gather_user_data(self, request:Request) -> UserModel:
        verified_token = await self._token.verify_token(request, self._token.ACCESS_TYPE)
        sub = int(verified_token.get('sub'))
        return await self._repo.get_user_for_auth_by_id(sub)
    
    @time_checker
    async def set_cookies(self, response:Response, tokens:dict) -> Response:
        settle = await self._token.set_secure_cookies(response, tokens)
        return settle
    
    @time_checker
    async def token_rotate(self, token):
        return self._token.rotate_tokens(self._repo.session, token, self._db)
    
    @time_checker
    async def logout(self, request:Request,  response:Response) -> Response:
        # gain token from request cookie
        verified_token = await self._token.verify_token_id(request, self._token.ACCESS_TYPE)
        user = await self._repo.get_user_for_auth_by_id(verified_token)
        logger.debug(f"User {user.login} tries to logout")
        # disable user
        await self._repo.disable_user(verified_token)
        return await self._token.clear_tokens(response)
    
    #async def password_change(email:str):pass