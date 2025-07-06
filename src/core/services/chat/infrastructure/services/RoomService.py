from typing import Dict, Optional, List, Set, DefaultDict
from collections import defaultdict
import uuid
import logging

logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self):
        # Structure: {room_type: {room_id: {'name': str, 'password': str, 'messages': list, 'clients':{} }}}
        self.rooms: Dict[str, Dict[str, Dict[str, str, list, set]]] = {}
        
    async def create_room(self, room_type: str, name: str, password: Optional[str] = None) -> str:
        #room_id = str(uuid.uuid4())
        if self.rooms.get(room_type) is None:
            self.rooms[room_type] = {}

        self.rooms[room_type][name] = {
                'name': name,
                'password': password,
                'messages': [],
                'clients':set()
            }

    async def add_message_to_room(self, room_type: str, room_name: str, message: Dict):
        if room_type in self.rooms and room_name in self.rooms[room_type]:
            self.rooms[room_type][room_name]['messages'].append(message)
            # Keep only the last N messages in memory
            self.rooms[room_type][room_name]['messages'] = self.rooms[room_type][room_name]['messages'][-50:]

    async def get_available_rooms(self) -> Dict[str, List[Dict]]:
        logger.debug(self.rooms.items())
        return {
            room_type: [
                {
                    'id': room_name,
                    'name': data['name'],
                    'has_password': data['password'] is not None,
                    'user_count': len(data['clients'])
                }
                for room_name, data in rooms.items()
            ]
            for room_type, rooms in self.rooms.items()
        }

    async def validate_room_access(self, room_type: str, room_name: str, password: Optional[str] = None) -> bool:
        room = self.rooms.get(room_type, {})
        logger.debug(room)
        exact_room = room.get(room_name)
        logger.debug(exact_room)
        logger.debug(self.rooms)
        if not exact_room:
            return False
            
        if room_type == 'private' and room['password'] and room['password'] != password:
            return False
            
        return True