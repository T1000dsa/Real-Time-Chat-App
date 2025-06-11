from fastapi import Response, Request, HTTPException
from datetime import timedelta, datetime, timezone
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from jose.exceptions import ExpiredSignatureError
from typing import Optional
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
        self.REFRESH_TOKEN_EXPIRE = timedelta(minutes=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS) # changed from days to minutes for test
        
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
        token = request.cookies.get(token_type)
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type")
        return payload
    
    @time_checker
    async def verify_token_unsafe(self, request: Request, token_type: str) -> dict:
        token = request.cookies.get(token_type)
        if not token:
            raise HTTPException(status_code=401, detail="Token missing")
        
        payload = jwt.decode(str(token), self.secret_key, algorithms=[self.algorithm], options={'verify_exp': False})
        if payload.get("type") != token_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type")
        
        return payload
    
    @time_checker   
    async def rotate_tokens(
        self, 
        request:Request,
        session: AsyncSession,
        token_repo:DatabaseTokenRepository
    ) -> Optional[dict]:
        """
        1. Token Verification
        2. If access token expired - > make new access token, if refresh token expired - > make both
        3. return token/tokens
        """
        new_access_token = None
        new_tokens = None
        try:
            try:
                # access token verification. If expired, JWT raises the ExpiredSignatureError 
                await self.verify_token(request, self.ACCESS_TYPE) 
                logger.info('access token is fine and not expired yet')
                # If here, everything is okay, access not expired yet.
            except ExpiredSignatureError as err: # Most likely would raised many times
                logger.info(err)
                access_data = await self.verify_token_unsafe(request, self.ACCESS_TYPE)
                new_access_token = await self.create_token(access_data, self.ACCESS_TOKEN_EXPIRE, self.ACCESS_TYPE)
                logger.info('New access token')

            await self.verify_token(request, self.REFRESH_TYPE)
            logger.info('refresh token is fine and not expired yet')

            """verified_refr_token_model = await token_repo.verificate_refresh_token(session, refresh_token)
            if verified_refr_token_model is None:
                pass"""

            # if here refr token not expired yet, but access may be expired

        except ExpiredSignatureError as err:
            logger.info(err)
            refresh_data = await self.verify_token_unsafe(request, self.REFRESH_TYPE)
            new_tokens = await self.create_tokens(refresh_data)
            logger.info('New pair of refresh and access tokens')

        if new_tokens: # if rotation was completed, return new tokens firstly
            logger.debug('Return new token pair')
            return new_tokens
        
        if new_access_token and new_tokens is None: # if just access token, return new_access token
            logger.debug('Return new access')
            return {self.ACCESS_TYPE:new_access_token}

        logger.debug('return nothing')
        return None


    @time_checker
    async def set_secure_cookies(self, response:Response, tokens:dict) -> Response:
        """This method should to set cookies in response body"""
        
        access_token = tokens.get(self.ACCESS_TYPE)
        refresh_token = tokens.get(self.REFRESH_TYPE)
        csrf_token = tokens.get(self.CSRF_TYPE)

        if access_token:
            response.set_cookie(
                key=self.ACCESS_TYPE,
                value=access_token,
                httponly=True,
                secure=settings.is_prod, # if in DEV, TEST -> False
                samesite="lax",
                max_age=self.ACCESS_TOKEN_EXPIRE,
                path="/"
                )
            
        if refresh_token:
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