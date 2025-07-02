from typing import Dict, Optional, List, Set, DefaultDict
from collections import defaultdict
import uuid
import logging

logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self):
        # Structure: {room_type: {room_id: room_data}}
        self.rooms: DefaultDict[str, Dict[str, Dict]] = defaultdict(dict)
        
    async def create_room(self, room_type: str, name: str, password: Optional[str] = None) -> str:
        room_id = str(uuid.uuid4())
        self.rooms[room_type][room_id] = {
            'name': name,
            'password': password,
            'clients': set(),
            'messages': []  # Store recent messages in memory
        }
        return room_id

    async def validate_room_access(self, room_type: str, room_id: str, password: Optional[str] = None) -> bool:
        room = self.rooms.get(room_type, {}).get(room_id)
        if not room:
            return False
            
        if room_type == 'private' and room['password'] and room['password'] != password:
            return False
            
        return True

    async def get_available_rooms(self) -> Dict[str, List[Dict]]:
        return {
            room_type: [
                {
                    'id': room_id,
                    'name': data['name'],
                    'has_password': data['password'] is not None,
                    'user_count': len(data['clients'])
                }
                for room_id, data in rooms.items()
            ]
            for room_type, rooms in self.rooms.items()
        }