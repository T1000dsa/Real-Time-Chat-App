from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional, Type
from datetime import datetime, timezone
import logging

from src.utils.time_check import time_checker
from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel
from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.auth_schema import RefreshToken

logger = logging.getLogger(__name__)

@time_checker
async def select_data_token(
    session: AsyncSession,
    hashed_token: str,
) -> Union[RefreshTokenModel, UserModel, None]:
    try:
        stmt = select(RefreshTokenModel).where(
                    RefreshTokenModel.token == hashed_token)
        return (await session.execute(stmt)).scalar_one_or_none()

    except SQLAlchemyError as e:
        logger.error(f"Database error in select_data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    
@time_checker
async def insert_data_token(
    session: AsyncSession,
    token_model: RefreshToken
) -> RefreshTokenModel:
    """Properly handles refresh token insertion with error handling"""
    try:
        token_model_res = RefreshTokenModel(
            user_id=token_model.user_id,
            token=token_model.token,
            expires_at=token_model.expires_at,
            revoked=token_model.revoked,
            replaced_by_token=token_model.replaced_by_token,
            family_id=token_model.family_id,
            previous_token_id=token_model.previous_token_id,
            # created_at is automatically set by the model
            device_info=token_model.device_info if hasattr(token_model, 'device_info') else None
        )
        
        session.add(token_model_res)
        await session.commit()
        await session.refresh(token_model_res)
        return token_model_res
        
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
async def delete_data_by_token(
    session: AsyncSession,
    token:str,
) -> None:
    try:
        await session.execute(
        delete(RefreshTokenModel)
        .where(RefreshTokenModel.token == token))
        await session.commit()

    except Exception as err:
        logger.critical(f'Something unpredictable: {err}')
        await session.rollback()
        raise err
    
@time_checker
async def delete_data_by_user(
    session: AsyncSession,
    user_id:int,
) -> None:
    try:
        await session.execute(
        delete(RefreshTokenModel)
        .where(RefreshTokenModel.user_id == user_id))
        await session.commit()

    except Exception as err:
        logger.critical(f'Something unpredictable: {err}')
        await session.rollback()
        raise err
        
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