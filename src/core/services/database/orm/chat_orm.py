from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging


from src.core.services.database.models.chat import MessageModel, DirectModel
from src.core.schemas.message_shema import MessageSchema, MessabeSchemaBase, DirectMessage, DirectScheme
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
        MessageModel.user_id == int(message_data.user)
        and
        MessageModel.room_id == message_data.room_type)
    res = (await session.execute(query)).scalars().all()[-40:]
    return res

@time_checker
async def select_messages_direct(
    session: AsyncSession,
    message_data:DirectMessage

) -> list[DirectModel]:
    query = select(DirectModel).where(
        (DirectModel.actor_id == message_data.actor_id and DirectModel.recipient_id == message_data.recipient_id) |
        (DirectModel.actor_id == message_data.recipient_id and DirectModel.recipient_id == message_data.actor_id)
    )
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
        user_id=int(message_data.user),
        message=message_data.message
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    logger.debug('Message saved!')

@time_checker
async def save_message_direct(
    session: AsyncSession,
    message_data:DirectScheme
):
    logger.debug('Saving direct message...')
    msg = DirectModel(
        actor_id=message_data.actor_id,
        recipient_id=message_data.recipient_id, 
        message=message_data.message, 
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    logger.debug('Message saved!')