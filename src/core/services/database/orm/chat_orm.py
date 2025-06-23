from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
import logging

from src.core.services.database.models.chat import MessageModel
from src.core.schemas.message_shema import MessageSchema, MessabeSchemaBase


logger = logging.getLogger(__name__)

async def select_messages(
    session: AsyncSession,
    message_data:MessabeSchemaBase
) -> MessageModel:
    query = select(MessageModel).where(MessageModel.room_id==message_data.room_id and MessageModel.user_id == message_data.user_id)
    res = (await session.execute(query)).scalars().all()[-20:]
    return res

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