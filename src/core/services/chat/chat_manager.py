from fastapi import WebSocket, HTTPException, Request
from typing import List, Dict, Set
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
list_mesagges = []
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # client_id: websocket
        self.client_rooms: Dict[str, Set[str]] = {}  # room_id: set(client_ids)
        self.client_to_rooms: Dict[str, Set[str]] = {}  # client_id: set(room_ids)
        self.message_history: List[Dict] = []

    async def connect(self, websocket: WebSocket, request:Request) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())
        self.active_connections[client_id] = websocket
        self.client_to_rooms[client_id] = set()
        logger.info(f"New connection: {client_id}")
        return client_id

    async def join_room(self, client_id: str, room_id: str):
        if client_id not in self.active_connections:
            raise HTTPException(404, "Client not connected")
        
        if room_id not in self.client_rooms:
            self.client_rooms[room_id] = set()
        
        self.client_rooms[room_id].add(client_id)
        self.client_to_rooms[client_id].add(room_id)
        logger.info(f"Client {client_id} joined room {room_id}")

    async def leave_room(self, client_id: str, room_id: str):
        if room_id in self.client_rooms and client_id in self.client_rooms[room_id]:
            self.client_rooms[room_id].remove(client_id)
            self.client_to_rooms[client_id].remove(room_id)
            logger.info(f"Client {client_id} left room {room_id}")

    async def send_to_room(self, room_id: str, message: str, sender_id: str = "system"):
        if room_id not in self.client_rooms:
            raise HTTPException(404, "Room not found")
        
        for client_id in list(self.client_rooms[room_id]):  # Create copy to avoid mutation
            try:
                await self.active_connections[client_id].send_text(message)
                await self._add_to_history(message, sender_id, room_id)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {str(e)}")
                await self.disconnect(client_id)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Disconnected: {client_id}")

    async def _add_to_history(self, message: str, sender: str = "system"):
        self.message_history.append({
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "message": message
        })
        # Keep only last 100 messages
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]

    async def send_to_client(self, client_id: str, message: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
            await self._add_to_history(message, "server")
            list_mesagges.append(message)
        else:
            raise HTTPException(404, "Client not connected")

    async def broadcast(self, message: str):
        for client_id in list(self.active_connections.keys()):  # Create copy to avoid mutation
            try:
                await self.send_to_client(client_id, message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {str(e)}")
                self.disconnect(client_id)

manager = ConnectionManager()