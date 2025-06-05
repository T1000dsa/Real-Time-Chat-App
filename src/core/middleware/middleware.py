from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response, RedirectResponse
import time
import logging
from typing import Optional

from src.utils.time_check import time_checker
from src.core.dependencies.auth_injection import get_auth_service, get_token_service
from src.core.config.auth_config import REFRESH_TYPE, ACCESS_TYPE
from src.core.config.config import settings
from src.core.dependencies.db_injection import db_helper

logger = logging.getLogger(__name__)

ignore_paths = {'/.well-known', '/ws/', f'{settings.prefix.api_data.prefix}/logout'}

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def token_refresh_middleware(request: Request, call_next):
        if any(request.url.path.startswith(path) for path in ignore_paths):
            return await call_next(request)
        
        logger.info(f'Incoming request from {request.url}')
        
        try:
            response = await call_next(request)
            
            # Only attempt refresh if we have a refresh token
            if refresh_token := request.cookies.get(REFRESH_TYPE): 
                token_service = await get_token_service()
                async with db_helper.async_session() as db:
                    auth_service = await get_auth_service(db, token_service=token_service)

                if request.url or request.url.path != f'{settings.prefix.api_data.prefix}/logout':

                    if await auth_service.token_service.is_token_expired(
                        request.cookies.get(ACCESS_TYPE), 
                        ACCESS_TYPE
                    ):
                        new_tokens = await auth_service.rotate_tokens(request)
                        await auth_service.token_service.set_secure_cookies(response, new_tokens)
            
            return response
            
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise
            logger.error(f"Middleware error: {exc}")
            return await call_next(request)