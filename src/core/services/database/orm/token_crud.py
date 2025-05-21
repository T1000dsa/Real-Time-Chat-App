from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional
from datetime import datetime, timezone
import logging

from src.core.services.database.models.refresh_token import RefreshTokenModel
from src.core.services.database.models.user import UserModel
from src.core.schemas.auth_schema import RefreshToken
from src.core.schemas.User import UserSchema
from src.core.config.auth_config import (
    pwd_context
)


logger = logging.getLogger(__name__)

async def select_data(
    session: AsyncSession,
    token: Optional[str] = None,
    user_id: Optional[int] = None,
    model_type: Union[RefreshToken, UserSchema] = RefreshToken
) -> Union[RefreshTokenModel, UserModel, None]:
    try:
        logger.debug(f"Selecting data with token={token}, user_id={user_id}, model_type={model_type}")
        
        if model_type == RefreshToken:
            stmt = select(RefreshTokenModel)
            if token:
                # Compare with all tokens using SQLAlchemy's ORM
                # This is inefficient but works for small datasets
                # For production, consider a different approach
                result = await session.execute(select(RefreshTokenModel))
                for token_record in result.scalars():
                    if pwd_context.verify(token, token_record.token):
                        return token_record
                return None
            if user_id:
                stmt = stmt.where(RefreshTokenModel.user_id == user_id)
        else:
            stmt = select(UserModel)
            if user_id:
                stmt = stmt.where(UserModel.id == user_id)
            if token:
                # For UserModel + token query
                result = await session.execute(select(RefreshTokenModel))
                for token_record in result.scalars():
                    if pwd_context.verify(token, token_record.token):
                        return await session.get(UserModel, token_record.user_id)
                return None

        if not token and not user_id:
            raise ValueError('Need to provide at least one argument (token or user_id)')

        result = (await session.execute(stmt)).scalar_one_or_none()
        logger.debug(f"Query result: {result}")
        return result

    except SQLAlchemyError as e:
        logger.error(f"Database error in select_data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    
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
    
async def delete_data(
    session: AsyncSession,
    token:Optional[str],
    user_id:Optional[int]
) -> None:
    try:
        logger.debug('in delete_data')
        if bool(token and user_id): # 1 1
                logger.debug('bool(token and user_id)')
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

async def delete_all_user_tokens(
        session:AsyncSession,
          data: UserModel
          ):
    try:
        await session.execute(
                delete(RefreshTokenModel)
                .where(RefreshTokenModel.user_id == data.id))
        await session.commit()
    except Exception as err:
        logger.critical(f'Something unpredictable: {err}')
    
async def get_refresh_token_data(session: AsyncSession, token:str) -> RefreshTokenModel:
    stm = (select(RefreshTokenModel).where(RefreshTokenModel.token == token))
    result = (await session.execute(stm)).scalars().all()
    valid_tokens:list[RefreshTokenModel] = []
    for i in result:
        if i.revoked:
            continue
        if i.expires_at <= datetime.now(timezone.utc):
            continue
        valid_tokens.append(i)

    freshest = sorted(valid_tokens, key=lambda x:x.created_at)[:-1]
    if freshest:
        return freshest


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
    
