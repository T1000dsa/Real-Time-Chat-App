from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response
import time
import logging
from typing import Optional

from src.utils.time_check import time_checker
from src.core.dependencies.auth_injection import get_auth_service, get_token_service
from src.core.dependencies.db_injection import db_helper
from src.core.config.auth_config import REFRESH_TYPE, ACCESS_TYPE

logger = logging.getLogger(__name__)

ignore_path = {'/.well-known', '/ws/'}

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def refresh_token(request: Request, call_next):
        if any(map(lambda x:request.url.path.startswith(x), ignore_path)):
            return await call_next(request)
        
        logger.info(f"Incoming request to: {request.url} Path: {request.url.path}")

        # First process the request
        response:Response = await call_next(request)
        
        # Add process time heade
        
        # Check if we should attempt token refresh
        if request.cookies:
            try:
                # Manually resolve dependencies
                token_service = await get_token_service()
                async with db_helper.async_session() as db:
                    auth_service = await get_auth_service(db, token_service=token_service)

                
                # Get refresh token from cookies
                access_token: Optional[str] = request.cookies.get(ACCESS_TYPE)
                refresh_token: Optional[str] = request.cookies.get(REFRESH_TYPE)

                if not await token_service.is_token_expired(access_token, ACCESS_TYPE):

                    return response
                
                
                if refresh_token:
                    try:
                        # Rotate tokens using the auth_service
                        new_tokens = await auth_service.rotate_tokens(request)
                        
                        #logger.debug(new_tokens)
                        # Create a new response based on the original one
                    
                        
                        # Set the new tokens in cookies
                        await auth_service.token_service.set_secure_cookies(
                            response=response,
                            tokens=new_tokens
                        )

                        return response
                        
                    except HTTPException as e:
                        logger.warning(f"Token refresh failed: {e.detail}")
                    except Exception as e:
                        logger.error(f"Token rotation failed: {e}")
            
            except Exception as err:
                logger.debug(f"Middleware error: {err}")
        
        return response