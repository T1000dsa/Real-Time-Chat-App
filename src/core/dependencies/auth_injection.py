from fastapi import Depends
from jose import JWTError, jwt
from typing import Annotated

from src.core.services.auth.token_service import TokenService
from src.core.services.auth.user_service import UserService
from src.core.dependencies.db_injection import DBDI
from src.core.services.database.models.user import UserModel
from src.core.config.config import settings
from src.core.config.auth_config import (
    oauth2_scheme, 
    credentials_exception, 
    inactive_user_exception
)


async def get_token_service() -> TokenService:
    return TokenService(
        secret_key=settings.jwt.key.get_secret_value(),
        algorithm=settings.jwt.algorithm
    )

async def get_auth_service(
    session: DBDI,
    token_service: TokenService = Depends(get_token_service)
) -> UserService:
    return UserService(
        session=session,
        token_service=token_service
    )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: UserService = Depends(get_auth_service)
) -> UserModel:
    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, settings.jwt.key.get_secret_value(), algorithms=[settings.jwt.algorithm])
        user_id: int = payload.get("sub")  # Changed from "use" to standard "sub"
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await auth_service.get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if not current_user.is_active:
        raise inactive_user_exception
    return current_user


GET_CURRENT_ACTIVE_USER = Annotated[UserModel, Depends(get_current_active_user)]