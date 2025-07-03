from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager


class DBRepo(ABC):
    """@time_checker
    async def save_message_db(self, session:AsyncSession, message:str, room_type:str, room_id:str, sender_id:str):
        message_data = MessageSchema(user_id=sender_id, room_type=room_type, room_id=room_id, message=message)
        await save_message(session, message_data)

    @time_checker
    async def receive_messages(self, session:AsyncSession, room_type:str, room_id:str, sender_id:str):
        message_data = MessabeSchemaBase(user_id=sender_id,room_type=room_type, room_id=room_id)
        return await select_messages(session, message_data)"""
    
    @abstractmethod
    async def save_message_db(self, session:AsyncSession, message:str, room_type:str, room_id:str, sender_id:str): ...

    @abstractmethod
    async def receive_messages(self, session:AsyncSession, room_type:str, room_id:str, sender_id:str): ...

    @abstractmethod
    async def load_message_history(
            self, 
            session:AsyncSession,
            connection_manager: ConnectionManager, 
            room_service: RoomService,  
            room_type: str, 
            room_id: str, 
            user_id: str, 
            limit: int = 50
            ): ...