from fastapi import Depends, Request
from typing import Annotated, Optional
import logging

from src.core.dependencies.db_injection import DBDI
from src.core.services.auth.infrastructure.repositories.DatabaseTokenRepository import DatabaseTokenRepository
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.services.auth.infrastructure.services.AuthProvider import AuthProvider
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.core.services.auth.infrastructure.services.User_Crud import UserService
from src.core.services.auth.infrastructure.services.EmailService import EmailService
from src.core.services.auth.infrastructure.services.UserService import UserServiceAuth
from src.core.services.auth.domain.models.user import UserModel
from src.core.exceptions.auth_exception import auth_demand_exception, inactive_user_exception


logger = logging.getLogger(__name__)

# JWT-service
def get_token_service() -> JWTService:
    return JWTService()

# database operations
def get_token_repo() -> DatabaseTokenRepository:
    return DatabaseTokenRepository()

# Hash operations
def get_hash_service() -> Bcryptprovider:
    return Bcryptprovider()

# Email operations
def get_email_service() -> EmailService:
    return EmailService()

def get_token_from_cookie(
        request: Request, 
        jwt_service:JWTService = Depends(get_token_service)
        ) -> Optional[str]:
    return request.cookies.get(jwt_service.ACCESS_TYPE)

# User service
def get_user_repo(
        hash_service = Depends(get_hash_service)
        ) -> UserService:
    return UserService(
        hash_service=hash_service
        )

def get_user_service(
        user_repo = Depends(get_user_repo),
        token_service = Depends(get_token_service)
) -> UserServiceAuth:
    user_service = UserServiceAuth(user_repo=user_repo, token_service=token_service)
    return user_service

# Main provider
def get_auth_provider(
        session:DBDI, 
        user_repo = Depends(get_user_repo), 
        hash_service = Depends(get_hash_service),
        token_service = Depends(get_token_service),
        db_repo = Depends(get_token_repo),
        emaiL_service = Depends(get_email_service),
        user_service = Depends(get_user_service)
        ) -> AuthProvider:
    return AuthProvider(
        session=session,
        user_repo=user_repo, 
        hash_service=hash_service, 
        token_service=token_service,
        db_repo=db_repo,
        email_service=emaiL_service,
        user_service=user_service
        )

# Current user dependency
async def get_current_user(
    request:Request,
    token: str = Depends(get_token_from_cookie),
    auth_service: AuthProvider = Depends(get_auth_provider)
) -> UserModel:
    if token is None:
        logger.info('Someone tried to reach endpoint')
        raise auth_demand_exception
    
    try:
        user = await auth_service._user.gather_user_data(request=request, session=auth_service.session)

        if user is None:
            logger.info('Someone tried to reach endpoint')
            raise auth_demand_exception
            
    except Exception as err:
        logger.error(f'{err}')
        raise err
        
    return user

# Current activated user dependency
async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if not current_user.is_active:
        logger.info('Someone tried to reach endpoint')
        raise inactive_user_exception
    return current_user

# Auth provider factory for middleware
def create_auth_provider(db_session):
    token_service = JWTService()
    hash_service = Bcryptprovider()
    token_repo = DatabaseTokenRepository()
    user_service = UserService(hash_service=hash_service)
    email_service = EmailService()
    user_service_auth = UserServiceAuth(user_repo=user_service, token_service=token_service)

    return AuthProvider(
        session=db_session,
        user_repo=user_service,
        hash_service=hash_service,
        token_service=token_service,
        db_repo=token_repo,
        email_service=email_service,
        user_service=user_service_auth
    )


# Current user dependency
async def get_current_user_for_email(
    request:Request,
    token: str = Depends(get_token_from_cookie),
    auth_service: AuthProvider = Depends(get_auth_provider)
) -> UserModel:
    if token is None:
        logger.info('Someone tried to reach endpoint')
        return None
    
    try:
        user = await auth_service._user.gather_user_data(request=request, session=auth_service.session)

        if user is None:
            logger.info('Someone tried to reach endpoint')
            return None
            
    except Exception as err:
        logger.error(f'{err}')
        return None
    return user


AuthDependency = Annotated[AuthProvider, Depends(get_auth_provider)]
GET_CURRENT_USER = Annotated[UserModel, Depends(get_current_user)]
GET_CURRENT_USER_FOR_EMAIL = Annotated[Optional[UserModel], Depends(get_current_user_for_email)]
GET_CURRENT_ACTIVE_USER = Annotated[UserModel, Depends(get_current_active_user)]