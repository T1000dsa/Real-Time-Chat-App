from fastapi import FastAPI, Request, Depends, HTTPException, Response
import logging

from src.core.config.config import settings, main_prefix
from src.core.dependencies.db_injection import db_helper
from src.utils.time_check import time_checker
from src.core.dependencies.auth_injection import create_auth_provider


ignore_paths = {"/.well-known/appspecific/com.chrome.devtools.json", f'{main_prefix}/login', f'{main_prefix}/logout'}
logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def refresh_token_middleware(request: Request, call_next):
        # Skip paths that don't need auth
        if request.url.path in ignore_paths:
            return await call_next(request)

        try:
            # Fast path for requests without auth cookies
            if not request.cookies:
                response = await call_next(request)
                return response

            async with db_helper.async_session() as db_session:
                auth = create_auth_provider(db_session)
                
                # Only attempt rotation if both tokens are present
                if all(k in request.cookies for k in [auth._token.ACCESS_TYPE, auth._token.REFRESH_TYPE]):
                    tokens = await auth.token_rotate(request)
                    if tokens:
                        response = await call_next(request)
                        await auth.set_cookies(response, tokens)
                        return response

                response = await call_next(request)
                return response

        except Exception as e:
            logger.error(f"Middleware error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")