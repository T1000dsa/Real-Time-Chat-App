from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from jose.exceptions import ExpiredSignatureError
import logging

from src.core.config.config import settings, main_prefix
from src.core.dependencies.db_injection import db_helper
from src.utils.time_check import time_checker
from src.core.dependencies.auth_injection import create_auth_provider

special_paths = {f'{main_prefix}/login', f'{main_prefix}/logout'}
ignore_paths = {"/.well-known/appspecific/com.chrome.devtools.json"}
logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def refresh_token_middleware(request: Request, call_next):
        # Skip middleware for special paths and ignored paths
        if request.url.path in request.url.path in ignore_paths:
            return await call_next(request)
            
        try:
            async with db_helper.async_session() as db_session:
                auth = create_auth_provider(db_session)
                response = None
                
                # Skip token processing if no cookies exist
                if not request.cookies:
                    return await call_next(request)
                    
                token = request.cookies.get(auth._token.ACCESS_TYPE)
                if not token:
                    return await call_next(request)
                    
                try:
                    # Try to get user data
                    user = await auth.gather_user_data(request)
                    logger.debug(f'Request to {request.url} from user {user.login}')
                    
                    # Attempt token rotation
                    tokens = await auth.token_rotate(request)
                    if tokens:
                        response = await call_next(request)
                        await auth.set_cookies(response, tokens)
                        return response
                        
                except ExpiredSignatureError as auth_error:
                    logger.warning(f"Authentication error: {auth_error}")
                    tokens = await auth.token_rotate(request)
                    if tokens:
                        response = await call_next(request)
                        await auth.set_cookies(response, tokens)
                        return response
                        
                except Exception as err:
                    logger.warning(f"Authentication error: {err}")
                    # If authentication fails, force logout
                    logout_response = await auth.logout(request)
                    return logout_response
                    
                # Default case - proceed with request
                return await call_next(request)
                
        except HTTPException as http_exc:
            logger.error(f"Middleware error: {http_exc}", exc_info=True)
            raise http_exc
        except Exception as exc:
            logger.error(f"Middleware error: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")