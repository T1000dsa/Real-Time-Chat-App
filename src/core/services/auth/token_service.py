from jose import JWTError, jwt, ExpiredSignatureError
from secrets import token_urlsafe
from pydantic import SecretStr
from fastapi import HTTPException, status, Response, Request
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.config.config import settings
from src.core.config.auth_config import (
    credentials_exception,
    ACCESS_TYPE,
    REFRESH_TYPE,
    CSRF_TYPE,
    pwd_context
)
from src.core.schemas.auth_schema import RefreshToken
from src.core.services.database.models.refresh_token import RefreshTokenModel
from src.core.services.database.models.user import UserModel
from src.utils.time_check import time_checker
from src.core.services.database.orm.token_crud import (
    insert_data, 
    delete_data, 
    delete_all_user_tokens, 
    get_refresh_token_data,
    select_data
)

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(
        self, 
        secret_key: SecretStr = settings.jwt.key,
        algorithm: str = settings.jwt.algorithm,
        pwd: CryptContext = pwd_context
    ):
        self.secret = secret_key.get_secret_value()
        self.algorithm = algorithm
        self.pwd_context = pwd

    @time_checker
    async def generate_csrf_token(self) -> str:
        return token_urlsafe(32)
    
    @time_checker
    async def is_token_expired(self, token: str, token_type: str) -> bool:
        try:
            # Just get expiration without full verify
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm], options={"verify_signature": False})
            if payload['type'] == token_type:
                return datetime.now(timezone.utc) > datetime.fromtimestamp(payload.get('exp'), timezone.utc)
        except JWTError:
            return True

    @time_checker
    async def verify_csrf(self, token: str, csrf:str) -> bool:
        """Verify CSRF token from cookie matches header"""
        
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            logger.debug(f'{payload.get("csrf")=} {csrf=}')
            if payload.get("csrf") != csrf:
                raise HTTPException(status_code=403, detail="CSRF token mismatch")
            return True
        except JWTError as err:
            logger.error(err)
            raise err
        
    @time_checker
    async def handle_refresh_token(self, session, refresh_token):
        try:
            # First try normal verification
            payload = await self.verify_token(refresh_token, REFRESH_TYPE)
            user_id = payload.get("sub")
        except ExpiredSignatureError:
            # If expired, decode without verification to get user_id
            try:
                unverified = jwt.decode(refresh_token, self.secret,  options={"verify_exp": False})
                user_id = unverified.get("sub")
            except JWTError as err:
                logger.error(f'Invalid token structure: {err}')
                raise credentials_exception
            
            # Check if this specific token was revoked
            if await self.is_token_revoked(session, refresh_token):
                raise credentials_exception
            
        except JWTError as err:
            logger.error(f'Token verification failed: {err}')
            raise credentials_exception
        
        # If we get here, token is either:
        # 1. Valid and not expired, or
        # 2. Expired but not revoked 
        new_tokens = await self.create_both_tokens({"sub": user_id}) # New csrf 
        old_token = await select_data(session, refresh_token, user_id)
        await self.store_refresh_token(
            session, 
            user_id, 
            new_tokens[REFRESH_TYPE], 
            old_token.id if old_token else None  # revoke the old one
        )
        return {
            ACCESS_TYPE: new_tokens.get(ACCESS_TYPE),
            REFRESH_TYPE: new_tokens.get(REFRESH_TYPE),
            CSRF_TYPE: new_tokens.get(CSRF_TYPE)
        }
        
    @time_checker
    async def create_token(self, data: dict, expires_delta: timedelta, token_type: str) -> str:
        """Base function for all tokens"""
        logger.debug('In create_token coroutine')
        to_encode = data.copy()
        date_now = datetime.now(timezone.utc)
        expire = date_now + expires_delta
        to_encode.update({
            "exp": expire, 
            "type": token_type,
            "iat": date_now
        })
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)
    
    @time_checker
    async def create_access_token(self, data: dict) -> str:
        return await self.create_token(
            data, 
            timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES),
            ACCESS_TYPE
        )
    
    @time_checker
    async def create_refresh_token(self, data: dict) -> str:
        return await self.create_token(
            data, 
            timedelta(minutes=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS),
            REFRESH_TYPE
        )
    
    @time_checker
    async def create_both_tokens(self, data: dict) -> dict:
        logger.debug("before generate_csrf_token")
        csrf_token = await self.generate_csrf_token()
        data_with_csrf = {**data, "csrf": csrf_token}
        logger.debug(f"before create tokens {data}")
        access_token = await self.create_access_token(data_with_csrf)
        refresh_token = await self.create_refresh_token(data_with_csrf)

        return {
            ACCESS_TYPE: access_token,
            REFRESH_TYPE: refresh_token,
            CSRF_TYPE: csrf_token
        }
    
    @time_checker
    async def create_singular_token(self, data: dict, token_type:str) -> dict:
        logger.debug(f"before create tokens {data}")

        new_token = ''

        if token_type == ACCESS_TYPE:
            new_token = await self.create_access_token(data)
        if token_type == REFRESH_TYPE:
            new_token = await self.create_refresh_token(data)

        return new_token
    
    @time_checker
    async def verify_token(self, token: str, token_type: str) -> dict:
        """Generic token verification method"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise credentials_exception
            return payload
        
        except JWTError as err:
            logger.error(f'{err}')
            raise err
        
    @time_checker
    def hash_token(self, token: str) -> str:
        """Hash token before storage"""
        return self.pwd_context.hash(token)
    
    @time_checker
    async def is_token_revoked(self, session: AsyncSession, token: str) -> bool:
        """Check if token was revoked"""
        hashed_token = self.hash_token(token)
        stored_token = await get_refresh_token_data(session, hashed_token)
        logger.debug(f"{stored_token=}")
        return stored_token is not None and stored_token.revoked
    
    @time_checker
    async def rotate_tokens(
        self, 
        session: AsyncSession,
        request: Request
    ) -> dict:
        """Simplified token rotation flow"""
        logger.debug('Trying to rotate tokens...')
        
        try:
            # Get tokens from request
            access_token = request.cookies.get(ACCESS_TYPE)
            refresh_token = request.cookies.get(REFRESH_TYPE)
            csrf_token = request.cookies.get(CSRF_TYPE)
            
            try:
                payload = await self.verify_token(refresh_token, REFRESH_TYPE)
            except:
                return await self.handle_refresh_token(session, refresh_token)
                
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Check for token reuse
            old_token_record = await self._get_token_record(session, refresh_token, user_id)
            if old_token_record and old_token_record.revoked:
                await self.revoke_token(session, old_token_record)
                logger.info(f'Token {old_token_record} already revoked')
                
            # Determine which tokens need refreshing
            access_expired = await self.is_token_expired(access_token, ACCESS_TYPE)
            refresh_expired = await self.is_token_expired(refresh_token, REFRESH_TYPE)
            
            new_tokens = {}
            if access_expired and not refresh_expired:
                new_tokens[ACCESS_TYPE] = await self.create_singular_token(
                    {"sub": user_id, "csrf": csrf_token}, 
                    ACCESS_TYPE
                )
            elif refresh_expired:
                new_tokens = await self.create_both_tokens({"sub": user_id})
                
            # Update old token record if new refresh token was created
            if new_tokens.get(REFRESH_TYPE):
                hashed_new_token = self.hash_token(new_tokens[REFRESH_TYPE])
                if old_token_record:
                    old_token_record.revoked = True
                    old_token_record.replaced_by_token = hashed_new_token
                await self.store_refresh_token(
                    session, 
                    user_id, 
                    new_tokens[REFRESH_TYPE], 
                    old_token_record.id if old_token_record else None
                )
                await session.commit()

            result = {
                ACCESS_TYPE: new_tokens.get(ACCESS_TYPE, access_token),
                REFRESH_TYPE: new_tokens.get(REFRESH_TYPE, refresh_token),
                CSRF_TYPE: csrf_token
            }
                
            logger.debug('Token rotation completed')
            logger.debug(result)

            return result
            
        except Exception as e:
            logger.error(f"Token rotation failed: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    async def _get_token_record(self, session: AsyncSession, token: str, user_id: int):
        """Helper to get token record"""
        return await select_data(
            session,
            token=token,
            user_id=user_id,
            model_type=RefreshToken
        )

    
    # Database operations (delegate to ORM)
    @time_checker
    async def store_refresh_token(
        self,
        session: AsyncSession,
        user_id: int,
        raw_token: str,
        previous_token_id: Optional[int] = None
    ) -> None:
        """Store refresh token with guaranteed naive UTC datetimes"""
        logger.debug(f'Store refr tokens. user_id={user_id} previous_token_id={previous_token_id}')
        try:
            # Create all datetimes as timezone-aware UTC first
            utc_now = datetime.now(timezone.utc)
            expires_at = utc_now + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)
            
            if previous_token_id is None:
                family_id = token_urlsafe(16)  # New token family
            else:
                previous_token = await session.get(RefreshTokenModel, previous_token_id)
                family_id = previous_token.family_id  # Continue same family

            token_data = RefreshToken(
                user_id=user_id,
                token=self.hash_token(raw_token),
                expires_at=expires_at,
                created_at=utc_now,
                family_id=family_id,
                previous_token_id=previous_token_id
            )
            
            await insert_data(session, token_data)
            
        except Exception as e:
            logger.error(f"Token storage failed: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store token"
            )
        
    @time_checker
    async def revoke_token(self, session: AsyncSession, token: Optional[str]=None, user_id:Optional[int]=None) -> None:
        """Take token OR user_ir. If none of them provided, will raised ValueError("Invalid data type provided")"""
        if token:
            token = self.hash_token(token)
        refresh_token = await select_data(token)
        logger.debug(refresh_token)
        if refresh_token:
            refresh_token.revoked = True
            await session.commit()


    @time_checker
    async def revoke_all_user_tokens(self, session: AsyncSession, data: RefreshTokenModel) -> None:
        await delete_all_user_tokens(session, data)

    async def set_secure_cookies(
        self,
        response: Response,
        tokens:dict
    ) -> Response:
        """Set HTTP-only and secure cookies"""
        
        access_token = tokens.get(ACCESS_TYPE)
        refresh_token = tokens.get(REFRESH_TYPE)
        csrf_token = tokens.get(CSRF_TYPE)

        logger.debug(f'{access_token} {refresh_token} {csrf_token}')
        

        response.set_cookie(
            key=ACCESS_TYPE,
            value=access_token,
            httponly=True,
            secure=settings.is_prod,  # Only send over HTTPS in production
            samesite="lax",
            max_age=timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES),
            path="/"
        )
        
        response.set_cookie(
        key=REFRESH_TYPE,
        value=refresh_token,
        httponly=True,
        secure=settings.is_prod,
        samesite="strict",
        max_age=timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS),
        path="/",  # Changed from "/auth/refresh" to "/"
        domain=None  # Explicitly set to None
    )
        
        if csrf_token:
            response.set_cookie(
                key=CSRF_TYPE,
                value=csrf_token,
                httponly=False,  # Accessible by JavaScript
                secure=settings.is_prod,
                samesite="strict",
                max_age=timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES),
                path="/"
            )

        return response

token_service = TokenService()