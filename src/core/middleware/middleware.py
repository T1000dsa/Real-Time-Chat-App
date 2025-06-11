from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jose.exceptions import ExpiredSignatureError
import logging

from src.core.dependencies.db_injection import db_helper
from src.utils.time_check import time_checker
from src.core.dependencies.auth_injection import create_auth_provider


logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def refresh_token_middleware(request: Request, call_next):
        try:
            # Manually build the dependency chain
           async with db_helper.async_session() as db_session:
                
                auth = create_auth_provider(db_session)
                if request.cookies:
                    token = request.cookies.get(auth._token.ACCESS_TYPE)
                    if token:
                        try:
                            user = await auth.gather_user_data(request)
                            logger.debug(f'Request to {request.url} from user {user.login}')
                                
                        except ExpiredSignatureError as auth_error:
                            logger.warning(f"Authentication error: {auth_error}")
                            response = RedirectResponse(url='/', status_code=302)
                            return await auth.logout(request, response)

                        except Exception as err:
                            logger.warning(f"Authentication error: {err}")
                            response = RedirectResponse(url='/', status_code=302)
                            return await auth.logout(request, response)
                            # Continue without user context for public endpoints
            
            # Proceed with the request
                response = await call_next(request)
                return response
                
        except HTTPException as http_exc:
            logger.error(f"Middleware error: {http_exc}", exc_info=True)
            raise http_exc
        except Exception as exc:
            logger.error(f"Middleware error: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")