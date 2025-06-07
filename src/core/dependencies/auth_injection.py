from fastapi import Depends
from typing import Annotated

from src.core.dependencies.db_injection import DBDI
from src.core.services.auth.domain.interfaces import TokenService, TokenRepository, HashService, AuthRepository, UserRepository
from src.core.services.auth.infrastructure.repositories.DatabaseTokenRepository import DatabaseTokenRepository
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.services.auth.infrastructure.services.AuthProvider import AuthProvider
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.core.services.auth.infrastructure.services.User_Crud import UserService

def get_token_service() -> JWTService:
    return JWTService()

def get_token_repo() -> DatabaseTokenRepository:
    return DatabaseTokenRepository()

def get_hash_service() -> Bcryptprovider:
    return Bcryptprovider()

def get_user_repo(
        session:DBDI, 
        hash_service = Depends(get_hash_service)
        ) -> UserService:
    return UserService(
        session=session, 
        hash_service=hash_service
        )

def get_auth_provider(
        user_repo = Depends(get_user_repo), 
        hash_service = Depends(get_hash_service),
        token_service = Depends(get_token_service),
        ) -> AuthProvider:
    return AuthProvider(
        user_repo=user_repo, 
        hash_service=hash_service, 
        token_service=token_service
        )

AuthDependency = Annotated[AuthProvider, Depends(get_auth_provider)]