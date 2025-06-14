from fastapi import WebSocket, HTTPException, Request
from typing import List, Dict, Set
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
list_mesagges = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # client_id: websocket
        self.rooms: dict = {}  # room_id: set(client_ids)

    async def connect(self, websocket: WebSocket, client_id:str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        return client_id

    async def join_room(self, client_id: str, room_id: str):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        await self.active_connections[client_id].send_text(message)

    async def broadcast_to_room(self, message: str, room_id: str, sender_id: str):
        if room_id in self.rooms:
            for client_id in list(self.rooms[room_id]):
                if client_id != sender_id:  # Optional: don't send back to sender
                    await self.send_personal_message(message, client_id)

    def disconnect(self, client_id: str):
        # Remove client from all rooms
        for room_id, clients in self.rooms.items():
            if client_id in clients:
                clients.remove(client_id)
        # Remove connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]


manager = ConnectionManager()