from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import logging

from src.core.config.auth_config import oauth2_scheme


router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, List[str]] = {}  # Track which rooms users are in

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def join_room(self, user_id: str, room_id: str):
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = []
        self.user_rooms[user_id].append(room_id)

    async def broadcast_to_room(self, message: str, room_id: str, sender_id: str = None):
        for user_id, rooms in self.user_rooms.items():
            if room_id in rooms and user_id in self.active_connections:
                if user_id != sender_id:  # Don't send back to sender
                    await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", user_id)
            await manager.broadcast(f"User #{user_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(f"User #{user_id} left the chat")