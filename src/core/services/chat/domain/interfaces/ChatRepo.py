from fastapi import WebSocket
from abc import ABC, abstractmethod
from typing import Optional


class ConnectionRepository(ABC):
    @abstractmethod
    async def connect(self, websocket: WebSocket, client_id: str): ...

    @abstractmethod
    def disconnect(self, client_id: str): ...

    @abstractmethod
    async def join_room(self, user_id: str, room_type: str, room_id: str, password: Optional[str] = None) -> bool: ...

    @abstractmethod
    async def leave_room(self, user_id: str, room_type: str, room_id: str): ...

    @abstractmethod
    async def send_personal_message(self, message: str, client_id: str): ...

    @abstractmethod
    def get_user_connections(self, user_id: str) -> Optional[WebSocket]: ...