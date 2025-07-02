from fastapi import WebSocket
from abc import ABC, abstractmethod
from typing import Optional

from src.core.services.chat.infrastructure.services.RoomService import RoomService


class ConnectionRepository(ABC):
    @abstractmethod
    async def connect(self, websocket: WebSocket, client_id: str): ...

    @abstractmethod
    def disconnect(self, room_service:RoomService, client_id: str): ...

    @abstractmethod
    async def join_room(self, user_id: str, room_type: str, room_id: str, password: Optional[str] = None) -> bool: ...

    @abstractmethod
    async def leave_room(self, room_service:RoomService, user_id: str, room_type: str, room_id: str): ...

    @abstractmethod
    async def send_personal_message(self, message: str, client_id: str): ...

    @abstractmethod
    def get_user_connections(self, user_id: str) -> Optional[WebSocket]: ...