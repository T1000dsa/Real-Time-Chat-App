from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional, Type
from datetime import datetime, timezone
from jose.exceptions import ExpiredSignatureError
import logging

from src.utils.time_check import time_checker
from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel
from src.core.schemas.auth_schema import RefreshToken

logger = logging.getLogger(__name__)

@time_checker
async def select_data_token(
    session: AsyncSession,
    hashed_token: str,
) -> Optional[RefreshTokenModel]:
    try:
        stmt = select(RefreshTokenModel).where(
                    RefreshTokenModel.token == hashed_token)
        res = await session.execute(stmt)
        result = res.scalar_one_or_none()
        return result

    except SQLAlchemyError as e:
        logger.error(f"Database error in select_data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    
async def new_token_insert(
    session: AsyncSession,
    token_scheme:RefreshToken
):
    try:
        token_model_res = RefreshTokenModel(
            token=token_scheme.token,
            expires_at=token_scheme.expires_at,
            revoked=token_scheme.revoked,
            replaced_by_token=token_scheme.replaced_by_token,
            family_id=token_scheme.family_id,
            device_info=token_scheme.device_info,
            previous_token_id=token_scheme.previous_token_id,
            user_id=token_scheme.user_id
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
    
    except Exception as err:
        await session.rollback()
        logger.error(err)
        raise err

@time_checker
async def update_data_token(
    session: AsyncSession,
    token_scheme: RefreshToken,
    old_token_scheme: RefreshToken
) -> RefreshTokenModel:
    """Properly handles refresh token insertion with error handling"""
    try:
        old_token_model = await select_data_token(session,old_token_scheme.token)
        old_token_model.revoked = True
        old_token_model.replaced_by_token = token_scheme.token
        session.add(old_token_model)

        await session.commit()
        await session.refresh(old_token_model)
        
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

@time_checker
async def revoke_refresh_token(session: AsyncSession, token:str) -> None:
    logger.debug('in revoke_refresh_token')
    try:
        stm = (select(RefreshTokenModel).where(RefreshTokenModel.token == token))
        result = await session.execute(stm)
        result = result.scalar_one_or_none()
        logger.debug(f"{result=}")
        result.revoked = True
        await session.commit()

    except Exception as err:
        logger.critical(f'Something unpredictable: {err}')
        await session.rollback()
        raise err


