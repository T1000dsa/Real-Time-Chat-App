from fastapi import WebSocket
from typing import Dict, Set, List
import logging


logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # client_id: websocket
        self.rooms: Dict[str, Dict[str, Set[str]]] = {}  # room_type: {room_id: set(client_ids)}
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id: set(room_ids)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        return client_id

    async def join_room(self, client_id: str, room_id: str):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                self.disconnect(client_id)

    async def broadcast_to_room(self, message: str, room_id: str, sender_id: str):
        if room_id in self.rooms:
            disconnected_clients = []
            for client_id in list(self.rooms[room_id]):
                if client_id != sender_id:
                    try:
                        await self.send_personal_message(message, client_id)
                    except:
                        disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)

    def disconnect(self, client_id: str):
        # Remove client from all rooms
        for room_id, clients in self.rooms.items():
            if client_id in clients:
                clients.remove(client_id)
        # Remove connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def create_room(self, room_type: str, room_id: str):
        """Create a new room of specific type"""
        if room_type not in self.rooms:
            self.rooms[room_type] = {}
        self.rooms[room_type][room_id] = set()

    async def join_room(self, user_id: str, room_type: str, room_id: str):
        """Join a user to a room"""
        if room_type not in self.rooms or room_id not in self.rooms[room_type]:
            await self.create_room(room_type, room_id)
            
        self.rooms[room_type][room_id].add(user_id)
        
        # Track which rooms user is in
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(f"{room_type}:{room_id}")

    async def leave_room(self, user_id: str, room_type: str, room_id: str):
        """Remove user from a room"""
        if room_type in self.rooms and room_id in self.rooms[room_type]:
            self.rooms[room_type][room_id].discard(user_id)
            
            # Clean up empty rooms
            if not self.rooms[room_type][room_id]:
                del self.rooms[room_type][room_id]
                
        # Update user's room tracking
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(f"{room_type}:{room_id}")

    async def broadcast_to_room(self, message: str, room_type: str, room_id: str, sender_id: str):
        """Send message to all in room except sender"""
        if room_type in self.rooms and room_id in self.rooms[room_type]:
            for user_id in list(self.rooms[room_type][room_id]):
                if user_id != sender_id and user_id in self.active_connections:
                    await self.active_connections[user_id].send_text(message)

    async def get_user_rooms(self, user_id: str) -> List[Dict[str, str]]:
        """Get list of rooms user is in"""
        return [{"type": r.split(":")[0], "id": r.split(":")[1]} 
                for r in self.user_rooms.get(user_id, [])]
    
    async def save_rooms_to_db(self):
        """Save active rooms to database for persistence"""
        pass

    async def create_protected_room(self, room_id, name, password):
        pass

    async def get_public_rooms(self):pass

    async def get_room_users(self, room_type: str, room_id: str) -> list[str]:
       """Get list of users in a room"""
       return list(self.rooms.get(room_type, {}).get(room_id, set()))


manager = ConnectionManager()