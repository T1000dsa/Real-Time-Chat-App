from fastapi import Response, Request
import logging

from src.core.schemas.User import UserSchema
from src.core.services.auth.domain.interfaces import AuthRepository
from src.core.services.auth.domain.models.user import UserModel
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.services.auth.infrastructure.services.User_Crud import UserService

logger = logging.getLogger(__name__)


class AuthProvider(AuthRepository):
    def __init__(self, user_repo: UserService, hash_service: Bcryptprovider, token_service:JWTService):
        self._repo = user_repo
        self._hash = hash_service
        self._token = token_service

    async def authenticate_user(self, username, password) -> dict:
        """
        Three-step authentication. 
        Firstly we search users in db, if we find them, return back to authenticate_user UserModel.
        Secondly we verify input password and actual hashed password that stored in database. 
        Thirdly if everything is okay gain tokens and sent them back toward login logic.
        """
        logger.debug(f'{username} tries to authorize...')
        # Fisrt step
        user:UserModel = await self._repo.get_user_for_auth(username)
        logger.debug(f'{user=}')
        if not user:
            #raise KeyError('user not found') # Temporary. Raise with expept factory, not from credential 
            return {}
        
        # Second step
        res = await self._hash.verify_password(password, user.password)
        if not res:
            #raise KeyError('username or password not matched') # actually username(login) is matched, just making vague response for security
            return {}
        
        # Third step 
        # gain_tokens
        user_data = {'sub':user.id}
        tokens = await self._token.create_tokens(user_data)

        return tokens
    
    async def register_user(self, user_data:UserSchema) -> None:
        pass

    async def gather_user_data(self, request:Request) -> dict:
        return {}
    
    async def set_cookies(self, response:Response, tokens:dict) -> Response:
        settle = await self._token.set_secure_cookies(response, tokens)
        return settle
        

    async def logout(self, request:Request,  response:Response) -> Response:
        return await self._token.clear_tokens(response)