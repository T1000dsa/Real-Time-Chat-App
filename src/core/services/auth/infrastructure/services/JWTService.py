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
        db_repo:DatabaseTokenRepository
    ) -> Optional[dict]:
        """
        1. Token Verification
        2. If access token expired - > make new access token, if refresh token expired - > make both
        3. return token/tokens
        """
        try:
            # First check refresh token (more critical)
            refresh_token = request.cookies.get(self.REFRESH_TYPE)
            
            if not refresh_token: # Extremely strange and rare situation
                return None
                
            try:
                refresh_payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
                if refresh_payload.get("type") != self.REFRESH_TYPE: # also Extremely strange and rare situation
                    return None
                
            except ExpiredSignatureError:
                # gain user data from unsafe verification (only if expired) and creating new tokens
                user_data = await self.verify_token_unsafe(request, self.REFRESH_TYPE)
                logger.debug('New token pair')
                result = await self.create_tokens(user_data)

                # gain old and new tokens
                old_refresh = request.get(self.REFRESH_TYPE)
                new_refresh = result.get(self.REFRESH_TYPE)
                old_token = await db_repo.verificate_refresh_token(session, old_refresh)

                # building new token scheme
                date = self.REFRESH_TOKEN_EXPIRE + datetime.now(timezone.utc)

                new_token_scheme = await db_repo.token_scheme_factory(
                    user_id=old_token.user_id,
                    token=refresh_token,
                    expires_at=date,
                    revoked=False,
                    replaced_by_token=None,
                    family_id=old_token.family_id,
                    previous_token_id=old_token.id,
                    device_info=old_token.device_info
                )
                # new token store
                await db_repo.store_new_refresh_token(session, new_token_scheme)
                
                # update old token, revoke and replace
                await db_repo.update_old_refresh_token(session, new_refresh, old_refresh)
                return result
            
            except Exception as err:
                logger.critical(err)
                return None

            # Then check access token
            access_token = request.cookies.get(self.ACCESS_TYPE)
            if access_token:
                try:
                    jwt.decode(access_token, self.secret_key, algorithms=[self.algorithm])
                    # Access token still valid, no rotation needed
                    logger.debug('Access token still valid')
                    return None
                except ExpiredSignatureError as err:
                    logger.info(err)
                    # Only access token expired - issue new access token
                    logger.debug('New access token')
                    return {
                        self.ACCESS_TYPE: await self.create_token(
                            {'sub': refresh_payload['sub']},
                            self.ACCESS_TOKEN_EXPIRE,
                            self.ACCESS_TYPE
                        )
                    }
                except Exception as err:
                    logger.critical(err)
                    return None
        
        except Exception as e:
            logger.error(f"Token rotation error: {e}")
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