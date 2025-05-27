from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional, Type
from datetime import datetime, timezone
import logging

from src.utils.time_check import time_checker
from src.core.services.database.models.refresh_token import RefreshTokenModel
from src.core.services.database.models.user import UserModel
from src.core.schemas.auth_schema import RefreshToken
from src.core.schemas.User import UserSchema
from src.core.config.auth_config import (
    pwd_context
)


logger = logging.getLogger(__name__)

@time_checker
async def select_data(
    session: AsyncSession,
    token: Optional[str] = None,
    user_id: Optional[int] = None,
    model_type: Union[Type[RefreshTokenModel], Type[UserModel]] = RefreshTokenModel
) -> Union[RefreshTokenModel, UserModel, None]:
    try:
        if model_type == RefreshTokenModel:
            if token:
                # OPTIMIZATION: Hash the token before comparing
                # This assumes you store hashed tokens in the database
                hashed_token = pwd_context.hash(token)
                stmt = select(RefreshTokenModel).where(
                    RefreshTokenModel.token == hashed_token
                )
                return (await session.execute(stmt)).scalar_one_or_none()
                
            if user_id:
                stmt = select(RefreshTokenModel).where(
                    RefreshTokenModel.user_id == user_id
                )
                return (await session.execute(stmt)).scalar_one_or_none()

        elif model_type == UserModel:
            if user_id:
                return await session.get(UserModel, user_id)
            if token:
                # First find the token, then get the user
                token_record = await select_data(session, token=token, model_type=RefreshTokenModel)
                if token_record:
                    return await session.get(UserModel, token_record.user_id)
                return None

    except SQLAlchemyError as e:
        logger.error(f"Database error in select_data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    
@time_checker
async def insert_data(
    session: AsyncSession,
    data: RefreshToken
) -> RefreshTokenModel:
    """Properly handles refresh token insertion with error handling"""
    try:
        token_model = RefreshTokenModel(
            user_id=data.user_id,
            token=data.token,
            expires_at=data.expires_at,
            revoked=data.revoked,
            replaced_by_token=data.replaced_by_token,
            family_id=data.family_id,
            previous_token_id=data.previous_token_id,
            # created_at is automatically set by the model
            device_info=data.device_info if hasattr(data, 'device_info') else None
        )
        
        session.add(token_model)
        await session.commit()
        await session.refresh(token_model)
        return token_model
        
    except IntegrityError as err:
        await session.rollback()
        logger.error(f"Database integrity error: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error inserting token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store token"
        )
    
@time_checker
async def delete_data(
    session: AsyncSession,
    token:Optional[str],
    user_id:Optional[int]
) -> None:
    try:
        logger.debug('in delete_data')
        if bool(token and user_id): # 1 1
                await session.execute(
                delete(RefreshTokenModel)
                .where(RefreshTokenModel.token == token and RefreshTokenModel.user_id == user_id))
                await session.commit()

        if bool(token and not user_id): # 1 0
                await session.execute(
                delete(RefreshTokenModel)
                .where(RefreshTokenModel.token == token))
                await session.commit()
            
        if bool(not token and user_id): # 0 1
                await session.execute(
                delete(RefreshTokenModel)
                .where(RefreshTokenModel.user_id == user_id))
                await session.commit()


    except ValueError as err:
        logger.error('Invalid data type provided')
        raise err
    
    except Exception as err:
        logger.critical(f'Something unpredictable: {err}')
        await session.rollback()
        raise err
    
@time_checker
async def delete_all_user_tokens(
        session:AsyncSession,
          data: RefreshTokenModel
          ):
    logger.debug(f'{data} {type(data)}')
    try:
        await session.execute(
                delete(RefreshTokenModel)
                .where(RefreshTokenModel.user_id == data.id))
        await session.commit()
    except Exception as err:
        logger.critical(f'Something unpredictable: {err}')
        
@time_checker
async def get_refresh_token_data(session: AsyncSession, token:str) -> RefreshTokenModel:
    logger.debug('in get_refresh_token_data')
    stm = (select(RefreshTokenModel).where(RefreshTokenModel.token == token))
    result = await session.execute(stm)
    result = result.scalars().all()
    valid_tokens:list[RefreshTokenModel] = []
    for item in result:
        if item.revoked:
            continue
        if item.expires_at <= datetime.now():
            item.revoked = True
            await session.commit()
            continue
        valid_tokens.append(item)

    freshest = sorted(valid_tokens, key=lambda x:x.created_at)[:-1]
    if freshest:
        return freshest
    logger.debug('get_refresh_token_data end')


async def nuclear_option(session: AsyncSession):
    """Delete ALL refresh tokens in the system (admin only)"""
    try:
        await session.execute(delete(RefreshTokenModel))
        await session.commit()
        logger.warning("Nuclear option executed - all refresh tokens purged")

    except Exception as e:
        await session.rollback()
        logger.critical(f"Failed nuclear option: {e}")
        raise e
    
