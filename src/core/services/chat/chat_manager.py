from fastapi import WebSocket
from typing import Dict, Set
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id → WebSocket
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id → set of room_ids
        self.room_users: Dict[str, Set[str]] = {}  # room_id → set of user_ids

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_rooms.setdefault(user_id, set())

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            # Leave all rooms when disconnecting
            for room_id in list(self.user_rooms.get(user_id, [])):
                await self.leave_room(user_id, room_id)
            del self.active_connections[user_id]

    async def join_room(self, user_id: str, room_id: str):
        self.user_rooms[user_id].add(room_id)
        self.room_users.setdefault(room_id, set()).add(user_id)
        
        # Notify others in the room
        join_message = json.dumps({
            "type": "system",
            "content": f"User {user_id} joined the room",
            "room_id": room_id
        })
        await self.broadcast_to_room(join_message, room_id, exclude=[user_id])

    async def leave_room(self, user_id: str, room_id: str):
        if user_id in self.user_rooms and room_id in self.user_rooms[user_id]:
            self.user_rooms[user_id].remove(room_id)
            if room_id in self.room_users and user_id in self.room_users[room_id]:
                self.room_users[room_id].remove(user_id)
            
            # Notify others in the room
            leave_message = json.dumps({
                "type": "system",
                "content": f"User {user_id} left the room",
                "room_id": room_id
            })
            await self.broadcast_to_room(leave_message, room_id)

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast_to_room(self, message: str, room_id: str, exclude: list = None):
        exclude = exclude or []
        if room_id in self.room_users:
            for user_id in self.room_users[room_id]:
                if user_id not in exclude and user_id in self.active_connections:
                    await self.active_connections[user_id].send_text(message)

    async def is_connected(self, user_id:str):
        return True if self.active_connections[user_id] else False


manager = ConnectionManager()