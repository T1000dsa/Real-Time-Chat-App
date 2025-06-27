from fastapi import WebSocket
from abc import ABC, abstractmethod
from typing import Optional


class MessageRepository(ABC):
    @abstractmethod
    async def process_message(self, message: str, room_id: str, sender_id: str): ...

    @abstractmethod
    async def save_message(self, message: str, room_id: str, sender_id: str): ...
    
    @abstractmethod
    async def broadcast_to_room(self, message: str, room_type:str, room_id: str, sender_id: str): ...

    @abstractmethod
    async def load_history(self, room_id: str, client_id: str): ...