from typing import Dict, Optional, List, Set
from collections import defaultdict
import uuid
import logging

from src.core.services.chat.domain.interfaces.RoomRepo import RoomRepository

logger = logging.getLogger(__name__)

class RoomService(RoomRepository):
    def __init__(self):
        self.rooms: Dict[str, Dict[str, Dict[str, Optional[str], Set]]] = defaultdict(dict)
        self.private_rooms: Dict[str, Dict] = {}  # room_id: {name, password, clients}
        self.protected_cons:dict = {}

    async def create_room(self, room_type: str, name: str, password: Optional[str] = None) -> str:
        room_id = str(uuid.uuid4())
        if room_type == 'private':
            self.private_rooms[room_id] = {
                'name': name,
                'password': password,
                'clients': set()
            }
        else:
            self.rooms[room_id] = {
                'name': name,
                'clients': set()
            }
        return room_id

    async def validate_room_access(self, room_id: str, password: Optional[str] = None) -> bool:
        if room_id in self.private_rooms:
            room = self.private_rooms[room_id]
            if room['password'] and room['password'] != password:
                return False
        return True

    async def get_available_rooms(self) -> Dict[str, List[Dict]]:
        return {
            'public': [{'id': k, 'name': v['name']} for k, v in self.rooms.items()],
            'private': [{
                'id': k, 
                'name': v['name'],
                'has_password': v['password'] is not None
            } for k, v in self.private_rooms.items()]
        }
    
    async def get_private_rooms(self) -> List[Dict]:
        """Get list of private rooms with their metadata"""
        return [
            {
                'id': room_id,
                'name': data['name'],
                'has_password': data['password'] is not None,
                'user_count': len(data['clients'])
            }
            for room_id, data in self.rooms.get('private', {}).items()
        ]