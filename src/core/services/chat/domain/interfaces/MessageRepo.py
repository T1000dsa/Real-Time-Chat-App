from abc import ABC, abstractmethod

from src.core.services.chat.infrastructure.services.RoomService import RoomService


class MessageRepository(ABC):
    @abstractmethod
    async def process_message(self, room_serv:RoomService, message: str, room_id: str, sender_id: str): ...

    @abstractmethod
    async def save_message(self, message: str, room_type:str, room_id: str, sender_id: str): ...
    
    @abstractmethod
    async def broadcast_to_room(self, message: str, room_type:str, room_id: str, sender_id: str): ...

    @abstractmethod
    async def broadcast_to_room(self, room_serv:RoomService, message: str, room_type:str, room_id: str, sender_id: str): ...