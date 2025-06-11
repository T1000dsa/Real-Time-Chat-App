from fastapi import Response, Request, HTTPException
from datetime import timedelta, datetime, timezone
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.services.auth.domain.interfaces.TokenService import TokenService
from src.core.services.auth.infrastructure.repositories.DatabaseTokenRepository import DatabaseTokenRepository
from src.core.config.config import settings
from src.utils.time_check import time_checker

logger = logging.getLogger(__name__)


class JWTService(TokenService):
    def __init__(self):
        self.secret_key = settings.jwt.key.get_secret_value()
        self.algorithm = settings.jwt.algorithm
        self.ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.REFRESH_TOKEN_EXPIRE = timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)
        
        self.ACCESS_TYPE = 'access'
        self.REFRESH_TYPE = 'refresh'
        self.CSRF_TYPE = 'csrf'

    @time_checker
    async def create_token(self, data: dict, expires_delta: timedelta, token_type: str) -> str:
        """Base function for all tokens"""
        to_encode = data.copy()
        date_now = datetime.now(timezone.utc)
        expire = date_now + expires_delta

        to_encode.update({
            "exp": expire, 
            "type": token_type,
            "iat": date_now
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    @time_checker
    async def create_tokens(self, data:dict) -> dict:
        access_token = await self.create_token(
            data=data, 
            expires_delta=self.ACCESS_TOKEN_EXPIRE, 
            token_type=self.ACCESS_TYPE
            )
        
        refresh_token = await self.create_token(
            data=data, 
            expires_delta=self.REFRESH_TOKEN_EXPIRE, 
            token_type=self.REFRESH_TYPE
            )
        return {
            self.ACCESS_TYPE:access_token, 
            self.REFRESH_TYPE:refresh_token
            }
    
    @time_checker
    async def verify_token(self, request:Request, token_type:str) -> dict:
        # Validates JWT signature and expiry
        token = request.cookies.get(token_type)
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
    
    @time_checker
    async def verify_token_id(self, request: Request, token_type: str) -> int:
        token = request.cookies.get(token_type)
        if not token:
            raise HTTPException(status_code=401, detail="Token missing")
        
        unverified = jwt.decode(str(token), self.secret_key, algorithms=[self.algorithm], options={'verify_exp': False})
        return int(unverified.get('sub'))
    
    @time_checker   
    async def rotate_tokens(
        self, 
        session: AsyncSession,
        refresh_token: str, 
        token_repo:DatabaseTokenRepository
    ) -> dict:
        """
        1. Token Verification
        """
    @time_checker
    async def set_secure_cookies(self, response:Response, tokens:dict) -> Response:
        """This method should to set cookies in response body"""
        
        access_token = tokens.get(self.ACCESS_TYPE)
        refresh_token = tokens.get(self.REFRESH_TYPE)
        csrf_token = tokens.get(self.CSRF_TYPE)

        response.set_cookie(
            key=self.ACCESS_TYPE,
            value=access_token,
            httponly=True,
            secure=settings.is_prod, # if in DEV, TEST -> False
            samesite="lax",
            max_age=self.ACCESS_TOKEN_EXPIRE,
            path="/"
            )
        
        response.set_cookie(
            key=self.REFRESH_TYPE,
            value=refresh_token,
            httponly=True,
            secure=settings.is_prod, # if in DEV, TEST -> False
            samesite="lax",
            max_age=self.REFRESH_TOKEN_EXPIRE,
            path="/"
            )
        if csrf_token:
            response.set_cookie(
            key=self.CSRF_TYPE,
            value=csrf_token,
            httponly=True,
            secure=settings.is_prod, # if in DEV, TEST -> False
            samesite="lax",
            max_age=self.ACCESS_TOKEN_EXPIRE,
            path="/"
            )

        return response

    @time_checker
    async def clear_tokens(self, response: Response) -> Response: 
        """This method should to purge all tokens"""
        response.delete_cookie(self.ACCESS_TYPE)
        response.delete_cookie(self.REFRESH_TYPE)
        response.delete_cookie(self.CSRF_TYPE)
        return response