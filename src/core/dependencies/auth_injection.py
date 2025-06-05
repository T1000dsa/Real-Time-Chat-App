from fastapi import Depends, Request
from jose import JWTError
from typing import Annotated

from src.core.services.auth.token_service import TokenService
from src.core.services.auth.user_service import UserService
from src.core.services.database.models.user import UserModel
from src.core.config.auth_config import credentials_exception, ACCESS_TYPE, inactive_user_exception
from src.core.dependencies.db_injection import DBDI

# Token service dependency
async def get_token_service() -> TokenService:
    return TokenService()

# Auth service dependency
async def get_auth_service(
    session: DBDI,
    token_service: Annotated[TokenService, Depends(get_token_service)]
) -> UserService:
    return UserService(session=session, token_service=token_service)

# Current user dependency
async def get_current_user(
    request: Request,
    auth_service: Annotated[UserService, Depends(get_auth_service)]
) -> UserModel:
    token = request.cookies.get(ACCESS_TYPE)
    if not token:
        raise credentials_exception
    
    try:
        payload = await auth_service.token_service.verify_token(token, ACCESS_TYPE)
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
            
        user = await auth_service.get_user_by_id(int(user_id))
        if not user:
            raise credentials_exception
            
        return user
        
    except JWTError:
        raise credentials_exception

# Active user dependency
async def get_current_active_user(
    user: Annotated[UserModel, Depends(get_current_user)]
) -> UserModel:
    if not user.is_active:
        raise inactive_user_exception
    return user

# Type aliases for cleaner route definitions
CurrentUser = Annotated[UserModel, Depends(get_current_user)]
ActiveUser = Annotated[UserModel, Depends(get_current_active_user)]
AuthService = Annotated[UserService, Depends(get_auth_service)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]