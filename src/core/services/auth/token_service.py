from jose import JWTError, jwt
from secrets import token_urlsafe
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
        secret_key: str = settings.jwt.key.get_secret_value(),
        algorithm: str = settings.jwt.algorithm,
        pwd: CryptContext = pwd_context
    ):
        self.secret = secret_key
        self.algorithm = algorithm
        self.pwd_context = pwd

    async def generate_csrf_token(self) -> str:
        return token_urlsafe(32)
        
    async def create_token(self, data: dict, expires_delta: timedelta, token_type: str) -> str:
        logger.debug("in create_token 1")
        """Base function for all tokens"""
        to_encode = data.copy()
        date_now = datetime.now(timezone.utc)
        expire = date_now + expires_delta

        to_encode.update({
            "exp": expire, 
            "type": token_type,
            "iat": date_now
        })
        logger.debug("in create_token 4")
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)
    
    async def create_access_token(self, data: dict) -> str:
        return await self.create_token(
            data, 
            timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES),
            ACCESS_TYPE
        )
    
    async def create_refresh_token(self, data: dict) -> str:
        return await self.create_token(
            data, 
            timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS),
            REFRESH_TYPE
        )
    
    async def create_both_tokens(self, data: dict) -> dict:
        csrf_token = await self.generate_csrf_token()
        data_with_csrf = {**data, "csrf": csrf_token}

        return {
            ACCESS_TYPE: await self.create_access_token(data_with_csrf),
            REFRESH_TYPE: await self.create_refresh_token(data_with_csrf),
            CSRF_TYPE: csrf_token
        }

    def verify_token(self, token: str, token_type: str) -> dict:
        """Generic token verification method"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                raise credentials_exception
            return payload
        except JWTError:
            raise credentials_exception
    
    def hash_token(self, token: str) -> str:
        """Hash token before storage"""
        return self.pwd_context.hash(token)
    
    async def is_token_revoked(self, session: AsyncSession, token: str) -> bool:
        """Check if token was revoked"""
        hashed_token = self.hash_token(token)
        stored_token = await get_refresh_token_data(session, hashed_token)
        return stored_token is not None and stored_token.revoked
    
    async def rotate_tokens(
        self, 
        session: AsyncSession,
        refresh_token: str
    ) -> dict:
        """
        Full token rotation flow:
        1. Verify old refresh token
        2. Check for token reuse
        3. Create new tokens
        4. Revoke old token
        """
        try:
            # 1. Verify token
            payload = self.verify_token(refresh_token, REFRESH_TYPE)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # 2. Get existing token record
            old_token_record = await select_data(
                session,
                token=refresh_token,  # Now passing raw token
                model_type=RefreshToken
            )

            logger.debug(f'{old_token_record=}')
            
            if not old_token_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
                
            # Check if token was already revoked
            if old_token_record.revoked:
                await self.revoke_all_user_tokens(session, user_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token was reused"
                )
            
            # 3. Create new tokens
            new_tokens = await self.create_both_tokens({"sub": user_id})
            hashed_new_token = self.hash_token(new_tokens[REFRESH_TYPE])
            
            # 4. Store new token and revoke old one
            await insert_data(session, RefreshToken(
                token=hashed_new_token,
                user_id=user_id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS),
                replaced_by_token=hashed_new_token,
                family_id=old_token_record.family_id,
                device_info=old_token_record.device_info
            ))
            
            # Revoke old token
            old_token_record.revoked = True
            old_token_record.replaced_by_token = hashed_new_token
            await session.commit()
            
            return new_tokens
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    
    # Database operations (delegate to ORM)
    async def store_refresh_token(
        self,
        session: AsyncSession,
        user_id: int,
        raw_token: str,
        previous_token_id: Optional[int] = None
    ) -> None:
        """Store refresh token with guaranteed naive UTC datetimes"""
        try:
            # Create all datetimes as timezone-aware UTC first
            utc_now = datetime.now(timezone.utc)
            expires_at = utc_now + timedelta(days=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS)
            
            # The NaiveDateTime will handle conversion to naive UTC
            token_data = RefreshToken(
                user_id=user_id,
                token=self.hash_token(raw_token),
                expires_at=expires_at,
                created_at=utc_now,
                family_id=token_urlsafe(16) if previous_token_id is None else (
                    await session.get(RefreshTokenModel, previous_token_id)
                ).family_id,
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

    async def revoke_token(self, session: AsyncSession, token: Optional[str], user_id:Optional[int]) -> None:
        """Take token OR user_ir. If none of them provided, will raised ValueError("Invalid data type provided")"""
        hashed_token = self.hash_token(token)
        await delete_data(session, hashed_token, user_id)

    async def revoke_all_user_tokens(self, session: AsyncSession, user_id: int) -> None:
        await delete_all_user_tokens(session, user_id)

    async def set_secure_cookies(
        self,
        response: Response,
        access_token: str,
        refresh_token: str,
        csrf_token: str = None
    ) -> Response:
        """Set HTTP-only and secure cookies"""
        response.set_cookie(
            key=ACCESS_TYPE,
            value=access_token,
            httponly=True,
            secure=settings.is_prod,  # Only send over HTTPS in production
            samesite="lax",
            max_age=timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES).seconds,
            path="/"
        )
        
        response.set_cookie(
        key=REFRESH_TYPE,
        value=refresh_token,
        httponly=True,
        secure=settings.is_prod,
        samesite="strict",
        max_age=settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
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
                max_age=timedelta(minutes=settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES).seconds,
                path="/"
            )

        return response
    
    async def verify_csrf(self, request: Request, token: str) -> bool:
        """Verify CSRF token from cookie matches header"""
        csrf_cookie = request.cookies.get("csrf_token")
        if not csrf_cookie:
            raise HTTPException(status_code=403, detail="CSRF token missing")
        
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("csrf") != csrf_cookie:
                raise HTTPException(status_code=403, detail="CSRF token mismatch")
            return True
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

token_service = TokenService()