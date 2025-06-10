from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response
import time
import logging
from typing import Optional

from src.core.dependencies.db_injection import db_helper
from src.utils.time_check import time_checker

# Import all your dependency-related classes and functions
from src.core.services.auth.infrastructure.repositories.DatabaseTokenRepository import DatabaseTokenRepository
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.services.auth.infrastructure.services.AuthProvider import AuthProvider
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.core.services.auth.infrastructure.services.User_Crud import UserService
from src.core.services.auth.domain.models.user import UserModel


logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def refresh_token_middleware(request: Request, call_next):
        try:
            # Manually build the dependency chain
           async with db_helper.async_session() as db_session:

            
            # Create all service instances manually
                token_service = JWTService()
                hash_service = Bcryptprovider()
                token_repo = DatabaseTokenRepository()
                
                # Create UserService with its dependencies
                user_service = UserService(session=db_session, hash_service=hash_service)
            
                # Create AuthProvider with all its dependencies
                auth_provider = AuthProvider(
                    user_repo=user_service,
                    hash_service=hash_service,
                    token_service=token_service
                )
                
                # Check cookies and user authentication
                if request.cookies:
                    token = request.cookies.get(token_service.ACCESS_TYPE)
                    
                    if token:
                        try:
                            user = await auth_provider.gather_user_data(request)
                            logger.debug(f'Request to {request.url} from user {user.login}')
                                
                        except Exception as auth_error:
                            logger.warning(f"Authentication error: {auth_error}")
                            # Continue without user context for public endpoints
                            pass
            
            # Proceed with the request
                response = await call_next(request)
                return response
                
        except HTTPException as http_exc:
            logger.error(f"Middleware error: {http_exc}", exc_info=True)
            raise http_exc
        except Exception as exc:
            logger.error(f"Middleware error: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")