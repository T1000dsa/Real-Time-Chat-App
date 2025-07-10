from typing import Dict, Optional, List
import logging



logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self):
        # Structure: {room_type: {room_id: {'name': str, 'password': str, 'messages': list, 'clients':{} }}}
        self.rooms: Dict[str, Dict[str, Dict[str, list, set]]] = {}

        # Structure: {actor_id: {recepient_id:str, recepients_id: set(), 'messages':list}
        self.directs: Dict[str, Dict[str, set]] = {}
        
    async def create_room(self, room_type: str, name: str, password: Optional[str] = None) -> str:
        if self.rooms.get(room_type) is None:
            self.rooms[room_type] = {}

        self.rooms[room_type][name] = {
                'password': password,
                'messages': [],
                'clients':set()
            }
        
    async def create_direct(self, actor_id: str, recepient_id: str):
        if self.directs.get(actor_id) is None:
            self.directs[actor_id] = {}

        self.directs[actor_id] = {
                'recepient_id':recepient_id,
                'messages': [],
                'recepients_id':set()
            }
        if recepient_id not in self.directs[actor_id]['recepients_id']:
            self.directs[actor_id]['recepients_id'].add(recepient_id)
    
    async def add_message_to_room(self, room_type: str, room_name: str, message: Dict):
        if room_type in self.rooms and room_name in self.rooms[room_type]:
            self.rooms[room_type][room_name]['messages'].append(message)
            # Keep only the last N messages in memory
            self.rooms[room_type][room_name]['messages'] = self.rooms[room_type][room_name]['messages'][-50:]

    async def get_available_rooms(self) -> Dict[str, List[Dict]]:
        logger.debug(self.rooms)
        return {
            room_type: [
                {
                    'has_password': data.get('password'),
                    'user_count': len(data.get('clients') if data.get('clients') else [])
                }
                for _, data in rooms.items()
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
    
    async def leave_direct(self, actor_id: str, recepient_id: str):
        logger.debug(self.directs)
        if recepient_id in self.directs[actor_id]:
            if self.directs[actor_id]['recepients_id']:
                self.directs[actor_id]['recepients_id'].discard(recepient_id)
                logger.info(f"User {actor_id} left {recepient_id}")

        logger.info(self.rooms)