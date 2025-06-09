from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response
import time
import logging
from typing import Optional

from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER, get_current_active_user, get_token_from_cookie
from src.core.dependencies.db_injection import db_helper
from src.utils.time_check import time_checker

logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    @time_checker
    async def refresh_token(request: Request, call_next):
        if request.cookies:
            logger.debug(f'Comming request to {request.url} from user')
            
        else:
            logger.debug(f'Comming request to {request.url}')

        response = await call_next(request)
        return response