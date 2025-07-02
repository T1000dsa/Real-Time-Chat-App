from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
import logging


from src.core.services.database.models.chat import MessageModel
from src.core.schemas.message_shema import MessageSchema, MessabeSchemaBase
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)

@time_checker
async def select_messages(
    session: AsyncSession,
    message_data:MessabeSchemaBase
) -> MessageModel:
    query = select(MessageModel).where(
        MessageModel.room_id == message_data.room_id 
        and 
        MessageModel.user_id == message_data.user_id
        and
        MessageModel.room_id == message_data.room_type)
    res = (await session.execute(query)).scalars().all()[-40:]
    return res

@time_checker
async def save_message(
    session: AsyncSession,
    message_data:MessageSchema
):
    logger.debug('Saving message...')
    message = MessageModel(
        room_id=message_data.room_id,
        room_type=message_data.room_type,
        user_id=message_data.user_id,
        message=message_data.message
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    logger.debug('Message saved!')