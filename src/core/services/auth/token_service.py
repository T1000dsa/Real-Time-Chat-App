from jose import JWTError, jwt
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

    async def generate_csrf_token(self) -> str:
        return token_urlsafe(32)
    
    async def token_expired(self, token:str, token_type:str) -> bool:
        try:
            payload = await self.verify_token(token, token_type)
            date = datetime.fromtimestamp(payload.get('exp'))
            date_now = datetime.now() # utc-0
            logger.debug(f"{date} {date_now} {date_now >= date}")

            if date_now >= date:
                return True
            else:
                return False
            
        except JWTError as err:
            logger.error(err)
            return True

    
    async def verify_csrf(self, token: str, csrf:str) -> bool:
        """Verify CSRF token from cookie matches header"""
        
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            if payload.get("csrf") != csrf:
                raise HTTPException(status_code=403, detail="CSRF token mismatch")
            return True
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token")
        
    async def create_token(self, data: dict, expires_delta: timedelta, token_type: str) -> str:
        """Base function for all tokens"""
        logger.debug('In create_token coroutine')
        to_encode = data.copy()
        date_now = datetime.now(timezone.utc)
        expire = date_now + expires_delta
        logger.debug(f"{date_now=} {expire=}")
        to_encode.update({
            "exp": expire, 
            "type": token_type,
            "iat": date_now
        })
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
    
    async def create_singular_token(self, data: dict, token_type:str) -> dict:
        logger.debug(f"before create tokens {data}")

        new_token = ''

        if token_type == ACCESS_TYPE:
            new_token = await self.create_access_token(data)
        if token_type == REFRESH_TYPE:
            new_token = await self.create_refresh_token(data)

        return new_token

    async def verify_token(self, token: str, token_type: str) -> dict:
        """Generic token verification method"""
        try:
            #logger.debug(f'before decode {self.secret}')
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            #logger.debug(payload)
            if payload.get("type") != token_type:
                raise credentials_exception
            return payload
        
        except JWTError as err:
            logger.error(f'{err}')
            raise err
    
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
        request: Request
    ) -> dict:
        """
        Full token rotation flow:
        1. Verify old refresh token
        2. Check for token reuse
        3. Create new tokens
        4. Revoke old token
        """
        logger.debug(f'Trying to rotate tokens...')
        try:
            # 1. Verify token
            access_token = request.cookies.get(ACCESS_TYPE)
            refresh_token = request.cookies.get(REFRESH_TYPE)
            csrf_token = request.cookies.get(CSRF_TYPE)
            payload = await self.verify_token(refresh_token, REFRESH_TYPE)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            new_access_token = ''
            hashed_new_token = ''
            new_tokens = {}

            old_token_record = await select_data(
                session,
                token=refresh_token,  # Now passing raw token
                user_id=user_id,
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
                await self.revoke_all_user_tokens(session, old_token_record)
                logger.info(f'Token {old_token_record} already revoked')
                #raise HTTPException(
                #    status_code=status.HTTP_401_UNAUTHORIZED,
                #    detail="Refresh token was reused"
                #)
            

            if await self.token_expired(access_token, ACCESS_TYPE) and not await self.token_expired(refresh_token, REFRESH_TYPE): # Expired access token and non expired refresh token
                data = {"sub": user_id, "csrf": csrf_token}
                new_access_token = await self.create_singular_token(data, ACCESS_TYPE)

            else:
                if await self.token_expired(refresh_token, REFRESH_TYPE):
                    new_tokens = await self.create_both_tokens({"sub": user_id})
                    hashed_new_token = self.hash_token(new_tokens[REFRESH_TYPE])


            old_token_record.revoked = True
            old_token_record.replaced_by_token = hashed_new_token

            if new_access_token or new_tokens:
                logger.debug('New tokens has been created successfully')
            else:
                logger.debug('Same tokens, no refresh happened')

                    
            if new_tokens:
                await self.store_refresh_token(session, user_id, new_tokens[REFRESH_TYPE], old_token_record.id)
                await session.commit()
                return new_tokens
            else:
                return {
                    ACCESS_TYPE:new_access_token if new_access_token else access_token,
                    REFRESH_TYPE:refresh_token,
                    CSRF_TYPE:csrf_token
                    }
            
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

    async def revoke_token(self, session: AsyncSession, token: Optional[str]=None, user_id:Optional[int]=None) -> None:
        """Take token OR user_ir. If none of them provided, will raised ValueError("Invalid data type provided")"""
        if token:
            token = self.hash_token(token)

        await delete_data(session, token, user_id)

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