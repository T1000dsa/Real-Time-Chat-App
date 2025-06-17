from fastapi import WebSocket
from typing import Dict, Set, List, Tuple
from collections import defaultdict
import logging


logger = logging.getLogger(__name__)

from typing import Dict, Set, List, Tuple, Optional
from collections import defaultdict
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id: websocket
        
        # Room structure: 
        # {
        #   "room_type": {
        #       "room_id": {
        #           "name": str,
        #           "password": Optional[str],
        #           "clients": Set[str]  # user_ids
        #       }
        #   }
        # }
        self.rooms: Dict[str, Dict[str, Dict[str, Optional[str], Set]]] = defaultdict(dict)
        
        # Track user's rooms: user_id -> set of (room_type, room_id) tuples
        self.user_rooms: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        return client_id
    
    def disconnect(self, client_id: str):
        # Remove from all rooms
        if client_id in self.user_rooms:
            for room_type, room_id in list(self.user_rooms[client_id]):
                if room_type in self.rooms and room_id in self.rooms[room_type]:
                    self.rooms[room_type][room_id]['clients'].discard(client_id)
                    
                    # Clean up empty rooms
                    if not self.rooms[room_type][room_id]['clients']:
                        del self.rooms[room_type][room_id]
    
        # Remove connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_rooms:
            del self.user_rooms[client_id]

    async def create_room(self, room_type: str, room_id: str):
        """Create a new room of specific type"""
        if room_type not in self.rooms:
            self.rooms[room_type] = {}
        self.rooms[room_type][room_id] = set()

    async def get_user_rooms(self, user_id: str) -> List[Dict[str, str]]:
        """Get list of rooms user is in"""
        return [{"type": r.split(":")[0], "id": r.split(":")[1]} 
                for r in self.user_rooms.get(user_id, [])]
    
    async def join_room(self, user_id: str, room_type: str, room_id: str, password: Optional[str] = None) -> bool:
        logger.debug(f"Attempting to join {user_id} to {room_type}/{room_id}")
        if room_type not in self.rooms:
            logger.debug(f"Room type {room_type} not found")
            return False
        
        if room_id not in self.rooms[room_type]:
            logger.debug(f"Room {room_id} not found in {room_type}")
            return False
            
        room = self.rooms[room_type][room_id]
        
        # Password check for private rooms
        logger.debug(f"{room['password']} {password}")
        if room_type == 'private' and room.get('password') and room['password'] != password:
            logger.debug("Password mismatch for private room")
            return False
            
        room['clients'].add(user_id)
        self.user_rooms[user_id].add((room_type, room_id))
        logger.debug(f"User {user_id} joined {room_type}/{room_id}. Current clients: {room['clients']}")
        return True

    async def leave_room(self, user_id: str, room_type: str, room_id: str):
        """Remove user from a room"""
        if room_type in self.rooms and room_id in self.rooms[room_type]:
            self.rooms[room_type][room_id]['clients'].discard(user_id)
            
            # Clean up empty rooms
            if not self.rooms[room_type][room_id]['clients']:
                del self.rooms[room_type][room_id]
                
        # Update user's room tracking
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard((room_type, room_id))

    async def create_protected_room(self, name: str, password: Optional[str] = None) -> str:
        """Create a new private room and return its ID"""
        room_id = str(uuid.uuid4())
        self.rooms['private'][room_id] = {
            'name': name,
            'password': password,
            'clients': set()
        }
        return room_id

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

        
    async def validate_room_access(self, user_id: str, room_type: str, room_id: str) -> bool:
        """Add validation logic for private rooms"""
        if room_type == 'private':
            # Add your access control logic here
            return True
        return True


    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                logger.debug(f'Sending msg {message[:10]} from {client_id}')
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                self.disconnect(client_id)

    async def broadcast_to_room(self, message: str, room_type: str, room_id: str, sender_id: str):
        if room_type in self.rooms and room_id in self.rooms[room_type]:
            room = self.rooms[room_type][room_id]
            disconnected_clients = []
            
            # Iterate over the clients in the room
            for user_id in list(room['clients']):  # Note: accessing room['clients']
                if user_id != sender_id:
                    try:
                        await self.send_personal_message(message, user_id)
                    except:
                        disconnected_clients.append(user_id)
            
            # Clean up disconnected clients
            for user_id in disconnected_clients:
                await self.leave_room(user_id, room_type, room_id)
                self.disconnect(user_id)
        

manager = ConnectionManager()