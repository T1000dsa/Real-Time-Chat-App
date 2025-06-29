from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional
import logging

from src.core.services.auth.domain.models.user import UserModel
from src.core.schemas.user import UserSchema
from src.core.services.auth.infrastructure.services.Bcryptprovider import Bcryptprovider
from src.utils.time_check import time_checker
from src.core.exceptions.auth_exception import false_activation_user_exception


logger = logging.getLogger(__name__)

@time_checker
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

@time_checker
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
    
@time_checker
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

@time_checker
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
    
@time_checker
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

@time_checker
async def user_activate(session:AsyncSession, user_id:int, activate:bool):
    query = select(UserModel).where(UserModel.id == user_id)
    res = await session.execute(query)
    user = res.scalar_one_or_none()
    logger.debug(f'{user=}')

    if user is None:
        raise ValueError(f"User with id {user_id} not found")
    
    #if user.is_active == activate:
        #raise false_activation_user_exception
    
    user.is_active = activate
    
    # Commit the changes
    await session.commit()
    await session.refresh(user)
    return user
    
@time_checker
async def delete_data_user(session:AsyncSession, user_id:int):
    try:
        stm = delete(UserModel).where(UserModel.id == user_id)
        await session.execute(stm)
        await session.commit()
        
    except Exception as err:
        logger.critical(err)
        await session.rollback()
        raise err
    
@time_checker
async def update_profile_file(session:AsyncSession, user:UserModel, data_dict:dict) -> None:
    logger.debug(f"{data_dict=}")
    try:
        old_photo = user.photo
        old_login = user.login
        old_email = user.email

        new_email = data_dict.get('email')
        new_photo = data_dict.get('photo')
        new_login = data_dict.get('login', None)

        if new_login:
            user.login = new_login

        if new_email:
            user.email = new_email

        if new_photo:
            user.photo = new_photo

        await session.commit()
        await session.refresh(user)

    except Exception as e:
        logger.error(f'Error update_profile_file user: {e}')
        await session.rollback()
        raise e
    
@time_checker   
async def update_password_by_email(session:AsyncSession, user:UserModel, new_pass:str, hash_service:Bcryptprovider, email:str):
    user_by_email = await select_user_email(session, email)
    if user_by_email and user:
        if user_by_email.id != user.id:
            raise KeyError('User email and provided email not matched! Please provide YOUR email!')
    else:
        raise KeyError("Such email doesnt exist!")
    try:
        if 129 > len(new_pass) > 0:
            user.password = await hash_service.hash_password(new_pass)
        else:
            raise KeyError('Password cant be more 128 or less than 0 characters')
            
        await session.commit()
        await session.refresh(user)
        logger.debug('Password was changed successfully!')

    except Exception as err:
        logger.error(err)
        await session.rollback()
        raise err
    
@time_checker  
async def give_all_active_users(session:AsyncSession):
    try:
        query = select(UserModel).where(UserModel.is_active == True)
        res = await session.execute(query)
        return res.scalars().all()

    except Exception as err:
        logger.error(err)
        raise err