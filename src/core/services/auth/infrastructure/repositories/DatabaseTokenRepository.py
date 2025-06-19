from sqlalchemy.ext.asyncio import AsyncSession
from jose.exceptions import ExpiredSignatureError
from jose import jwt
from fastapi import Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from src.core.schemas.auth_schema import RefreshToken
from src.core.schemas.message_shema import MessageSchema, MessabeSchemaBase
from src.core.services.auth.infrastructure.services.JWTService import JWTService
from src.core.services.auth.domain.interfaces.TokenRepository import TokenRepository
from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel
from src.core.services.database.orm.token_crud import (
    select_data_token, 
    update_data_token,
    revoke_refresh_token,
    new_token_insert
    )
from src.core.services.database.orm.chat_orm import(
    select_messages,
    save_message
)
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)

class DatabaseTokenRepository(TokenRepository):
    @time_checker
    async def store_new_refresh_token(self, session:AsyncSession, token_schema:RefreshToken):
        await new_token_insert(session, token_schema)

    @time_checker
    async def refresh_token_flow(
        self, 
        request:Request,
        session: AsyncSession,
        jwt_service:JWTService
        ):
        """
        1. Token Verification
        2. If access token expired - > make new access token, if refresh token expired - > make both
        3. return token/tokens
        """
        try:
            # First check refresh token (more critical)
            refresh_token = request.cookies.get(jwt_service.REFRESH_TYPE)
            
            if not refresh_token: # Extremely strange and rare situation
                logger.error(refresh_token)
                return None
                
            try:
                refresh_payload = jwt.decode(refresh_token, jwt_service.secret_key, algorithms=[jwt_service.algorithm])
                if refresh_payload.get("type") != jwt_service.REFRESH_TYPE: # also Extremely strange and rare situation
                    logger.error('Refresh payloads error')
                    return None
                
            except ExpiredSignatureError:
                # gain user data from unsafe verification (only if expired) and creating new tokens
                user_data = await jwt_service.verify_token_unsafe(request, jwt_service.REFRESH_TYPE)
                logger.debug('New token pair')
                result = await jwt_service.create_tokens(user_data)

                # gain old and new tokens
                old_refresh = request.cookies.get(jwt_service.REFRESH_TYPE)
                new_refresh = result.get(jwt_service.REFRESH_TYPE)
                old_token = await self.verificate_refresh_token(session, old_refresh)

                logger.debug(f"{new_refresh=}")
                logger.debug(f"{old_refresh=}")

                logger.debug(f"{old_token=}")

                # building new token scheme
                date = jwt_service.REFRESH_TOKEN_EXPIRE + datetime.now(timezone.utc)

                if old_token:
                    new_token_scheme = await self.token_scheme_factory(
                        user_id=old_token.user_id,
                        token=new_refresh,
                        expires_at=date,
                        revoked=False,
                        replaced_by_token=None,
                        family_id=old_token.family_id,
                        previous_token_id=old_token.id,
                        device_info=old_token.device_info
                    )
                else:
                    new_token_scheme = await self.token_scheme_factory(
                        user_id=user_data.get('sub'),
                        token=new_refresh,
                        expires_at=date,
                        revoked=False,
                        replaced_by_token=None,
                        family_id=str(uuid.uuid4()),
                        previous_token_id=None,
                        device_info=None
                    )

                # new token store
                await self.store_new_refresh_token(session, new_token_scheme)
                
                # update old token, revoke and replace
                await self.update_old_refresh_token(session, new_token_scheme, old_token)
                return result
            
            except Exception as err:
                logger.critical(err)
                return None

            # Then check access token
            access_token = request.cookies.get(jwt_service.ACCESS_TYPE)
            if access_token:
                try:
                    await jwt_service.verify_token(request, jwt_service.ACCESS_TYPE)
                    # Access token still valid, no rotation needed
                    logger.debug('Access token still valid')
                    return None
                except ExpiredSignatureError as err:
                    logger.info(err)
                    # Only access token expired - issue new access token
                    logger.debug('New access token')
                    return {
                        jwt_service.ACCESS_TYPE: await jwt_service.create_token(
                            {'sub': refresh_payload['sub']},
                            jwt_service.ACCESS_TOKEN_EXPIRE,
                            jwt_service.ACCESS_TYPE
                        )
                    }
                except Exception as err:
                    logger.critical(err)
                    return None
        
        except Exception as e:
            logger.error(f"Token rotation error: {e}")
            return None

    @time_checker
    async def update_old_refresh_token(self, session:AsyncSession,  token:RefreshToken, old_token:RefreshTokenModel) -> None:
        await update_data_token(session, token, old_token)

    @time_checker
    async def revoke_token(self, session:AsyncSession, token: str) -> None:
        await revoke_refresh_token(session, token)
        
    @time_checker
    async def verificate_refresh_token(self, session:AsyncSession, token:str) -> Optional[RefreshTokenModel]:
        return await select_data_token(session, token)
    
    @time_checker
    async def token_scheme_factory(self, **kwargs) -> RefreshToken:
        return RefreshToken(**kwargs)
    
    @time_checker
    async def save_message_db(self, session:AsyncSession, message:str, room_id:str, sender_id:str):
        message_data = MessageSchema(user_id=sender_id, room_id=room_id, message=message)
        await save_message(session, message_data)

    @time_checker
    async def receive_messages(self, session:AsyncSession, room_id:str, sender_id:str):
        message_data = MessabeSchemaBase(user_id=sender_id, room_id=room_id)
        return await select_messages(session, message_data)