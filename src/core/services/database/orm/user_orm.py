from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional
import logging

from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.user import UserSchema
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider


logger = logging.getLogger(__name__)

async def select_data_user_id(
        session: AsyncSession,
        user_id:int
        ) -> Optional[UserModel]:
    try:
        query = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(query)
        data_user =  result.scalar_one_or_none()

        if not data_user: # if data_user is none its will raise an error
            return None
        return data_user
    
    except Exception as err:
        logger.error(f"Failed to select user data: {str(err)}")
        raise err

async def select_data_user(
    session: AsyncSession,
    login: str
) -> Optional[UserModel]:
    try:
        query = select(UserModel).where(UserModel.login == login)
        result = await session.execute(query)
        data_user =  result.scalar_one_or_none()
        if not data_user:
            return None
        else:
            return data_user

    except Exception as err:
        logger.error(f"Failed to select user data: {str(err)}")
        raise err
    
async def select_user_email(
    session: AsyncSession,
    email:str
    ) -> Optional[UserModel]:
    try:
        stm = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stm)
        return result.scalar_one_or_none()
    
    except Exception as err:
        logger.error(f"Failed to select user data: {str(err)}")
        raise err

    
async def insert_data_user(
    session: AsyncSession,
    data: UserSchema,
    hash_service:Bcryptprovider
) -> Optional[UserModel]:
    try:
        res = UserSchema.model_validate(data, from_attributes=True)
        user_data = {i: k for i, k in res.model_dump().items() if i != 'password_again'}
        logger.debug(f"{user_data=}")
        new_data = UserModel(**user_data)
        new_data.password = await hash_service.hash_password(new_data.password)
        session.add(new_data)
        await session.commit()
        await session.refresh(new_data)
        logger.debug('Create user success')
        return new_data

        
    except IntegrityError as err:
        logger.info(f'{err}') # user already exists
        await session.rollback()
        raise err
        
    except Exception as e:
        logger.error(f'Error creating user: {e}')
        await session.rollback()
        raise e

async def update_data_user(
            session:AsyncSession,
            data_id:int=None, 
            data:UserSchema=None
            ):
    if type(data) == UserSchema:
        res = UserSchema.model_validate(data, from_attributes=True)
        stm = (update(UserModel).where(UserModel.id==data_id).values(**res))

        await session.execute(stm)
        await session.commit()

async def user_activate(session:AsyncSession, user_id:int, activate:bool):
    query = select(UserModel).where(UserModel.id == user_id)
    res = await session.execute(query)
    user = res.scalar_one_or_none()
    logger.debug(f'{user=}')

    if user is None:
        raise ValueError(f"User with id {user_id} not found")
    
    user.is_active = activate
    
    # Commit the changes
    await session.commit()
    await session.refresh(user)
    return user
    

async def delete_data_user(session:AsyncSession, user_id:int):
    try:
        stm = delete(UserModel).where(UserModel.id == user_id)
        await session.execute(stm)
        await session.commit()
        
    except Exception as err:
        logger.critical(err)
        await session.rollback()
        raise err
    
async def update_profile_file(session:AsyncSession, user:UserModel, data_dict:dict) -> None:
    logger.debug(f"{data_dict=}")
    try:
        old_photo = user.photo
        user.email = data_dict.get('email')
        user.photo = data_dict.get('photo')
        if user.photo != old_photo:
            if user.photo is None:
                user.photo = old_photo

        await session.commit()
        await session.refresh(user)

    except Exception as e:
        logger.error(f'Error deleting user: {e}')
        await session.rollback()
        raise e