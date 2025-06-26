from fastapi import WebSocket
from abc import ABC, abstractmethod
from typing import Optional, Dict, List


class RoomRepository(ABC):
    @abstractmethod
    async def create_room(self, room_type: str, name: str, password: Optional[str] = None) -> str: ...

    @abstractmethod
    async def validate_room_access(self, room_id: str, password: Optional[str] = None) -> bool: ...

    @abstractmethod
    async def get_available_rooms(self) -> Dict[str, List[Dict]]: ...