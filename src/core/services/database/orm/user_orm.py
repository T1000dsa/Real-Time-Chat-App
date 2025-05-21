from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
from typing import Union, Optional
import logging

from src.core.services.database.models.user import UserModel
from src.core.schemas.User import UserSchema as User_pydantic


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
    username: str,
    password: str
) -> Optional[UserModel]:
   
    try:
        query = select(UserModel).where(UserModel.username == username)
        result = await session.execute(query)
        data_user =  result.scalar_one_or_none()
        if not data_user: # if data_user is none its will raise an error
            return None
        else:
            if data_user.check_password(password): # if password is validates properly user returns and return None in any else cases
                return data_user
    

    except Exception as err:
        logger.error(f"Failed to select user data: {str(err)}")
        raise err
    
async def select_user_email(
    session: AsyncSession,
    data: Union[User_pydantic, str, int]
    ) -> Optional[UserModel]:
    try:
        if isinstance(data, str):
            query = select(UserModel).where(UserModel.email == data)
            

        result = await session.execute(query)
        return result.scalar_one_or_none()

    except ValueError as err:
        logger.error(f"select_user_email doesn't support such method {type(data)} {str(err)}")
        raise err
    
    except Exception as err:
        logger.error(f"Failed to select user data: {str(err)}")
        raise err

    
async def insert_data(
    session: AsyncSession,
    data: User_pydantic = None
) -> None:
    try:
        if isinstance(data, User_pydantic):
            res = User_pydantic.model_validate(data, from_attributes=True)
            user_data = {i: k for i, k in res.model_dump().items() if i != 'password_again'}
            new_data = UserModel(**user_data)
            new_data.set_password(new_data.password)
            session.add(new_data)
            await session.commit()
            await session.refresh(new_data)  # Refresh to get any database-generated values
            logger.debug('Create user success')
            return new_data
        else:
            logger.error('Invalid data type provided')
            raise ValueError("Invalid data type provided")
        
    except IntegrityError as err:
        logger.info(f'{err}') 
        raise err
        
    except Exception as e:
        logger.error(f'Error creating user: {e}')
        await session.rollback()
        raise e

async def update_data(
            session:AsyncSession,
            data_id:int=None, 
            data:User_pydantic=None
            ):
    if type(data) == User_pydantic:
        res = User_pydantic.model_validate(data, from_attributes=True)
        stm = (update(UserModel).where(UserModel.id==data_id).values(**res))

        await session.execute(stm)
        await session.commit()

async def delete_users(
            session:AsyncSession
            ):

    stm = (delete(UserModel)) 

    await session.execute(stm)
    await session.commit()

async def get_all_users(session:AsyncSession):
    query = select(UserModel)
    res = await session.execute(query)
    result = res.scalars().all()
    return result

async def user_activate(session:AsyncSession, user_id:int, activate:bool):
    query = select(UserModel).where(UserModel.id == user_id)
    user = (await session.execute(query)).scalar_one_or_none()

    if user is None:
        raise ValueError(f"User with id {user_id} not found")
    
    user.is_active = activate
    
    # Commit the changes
    await session.commit()
    
    # Refresh the user object if needed
    await session.refresh(user)
    
    return user
    