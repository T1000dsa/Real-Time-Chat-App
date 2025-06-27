from fastapi import WebSocket
from typing import Dict, Set, Optional
from collections import defaultdict
import logging

from src.core.services.chat.domain.interfaces.ChatRepo import ConnectionRepository


logger = logging.getLogger(__name__)


class ConnectionManager(ConnectionRepository):
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, Set[str]] = defaultdict(set)  # user_id: set(room_ids)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        return client_id

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_rooms:
            del self.user_rooms[client_id]

    async def join_room(self, user_id: str, room_type: str, room_id: str, password: Optional[str] = None) -> bool:
        logger.debug(f"Attempting to join {user_id} to {room_type}/{room_id}")
        logger.debug(self.user_rooms)
        if room_type not in self.user_rooms:
            logger.debug(f"Room type {room_type} not found")
            return False
        
        if room_id not in self.user_rooms[room_type]:
            logger.debug(f"Room {room_id} not found in {room_type}")
            return False
            
        room = self.user_rooms[room_type][room_id]
        
        # Password check for private rooms
        if room_type == 'private' and room.get('password') and room['password'] != password:
            logger.debug("Password mismatch for private room")
            return False
            
        room['clients'].add(user_id)
        self.user_rooms[user_id].add((room_type, room_id))
        logger.debug(f"User {user_id} joined {room_type}/{room_id}. Current clients: {room['clients']}")
        return True
    
    async def leave_room(self, user_id: str, room_type: str, room_id: str):
        if room_type in self.user_rooms and room_id in self.user_rooms[room_type]:
            self.user_rooms[room_type][room_id]['clients'].discard(user_id)
            
            # Clean up empty rooms
            if not self.user_rooms[room_type][room_id]['clients']:
                del self.user_rooms[room_type][room_id]
                
        # Update user's room tracking
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard((room_type, room_id))

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                self.disconnect(client_id)

    def get_user_connections(self, user_id: str) -> Optional[WebSocket]:
        return self.active_connections.get(user_id)