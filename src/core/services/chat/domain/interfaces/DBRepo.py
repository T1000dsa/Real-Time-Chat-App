from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager


class DBRepo(ABC):
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