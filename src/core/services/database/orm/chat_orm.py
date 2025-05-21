from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import select, update, delete, join
import logging

from src.core.services.database.models.chat import Message


logger = logging.getLogger(__name__)

async def save_message(
    session: AsyncSession,
    room_id: str,
    user_id: str,
    content: str
) -> Message:
    message = Message(
        room_id=room_id,
        user_id=user_id,
        content=content
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message