from fastapi import Response

from src.core.services.auth.domain.interfaces import AuthRepository
from src.core.services.auth.domain.models.user import UserModel
from src.core.services.auth.infrastructure import Bcryptprovider, JWTService, UserService


class AuthProvider(AuthRepository):
    def __init__(self, user_repo: UserService, hash_service: Bcryptprovider, token_service:JWTService):
        self._repo = user_repo
        self._hash = hash_service
        self._token = token_service

    async def authenticate_user(self, username, password) -> UserModel:
        """
        Three-step authentication. 
        Firstly we search users in db, if we find them, return back to authenticate_user UserModel.
        Secondly we verify input password and actual hashed password that stored in database. 
        Thirdly if everything is okay gain tokens and settle toward user's cookies.
        """
        # Fisrt step
        user:UserModel = await self._repo.get_user_for_auth(username)
        if not user:
            raise KeyError('user not found') # Temporary. Raise with expept factory, not from credential 
        
        # Second step
        if not self._hash.verify_password(user.password, password):
            raise KeyError('username or password not matched') # actually username(login) is matched, just making vague response for security
        
        # Third step 
        # gain_tokens
        # set_tokens 
        return user
        

    async def logout(self, response:Response) -> Response:
        return await self._token.clear_tokens(response)