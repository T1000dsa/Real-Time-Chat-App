from fastapi import WebSocket
from typing import Dict, Set, Optional, DefaultDict
from collections import defaultdict
import logging

from src.core.services.chat.infrastructure.services.RoomService import RoomService

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id: WebSocket
        self.active_connections: Dict[str, WebSocket] = {}


    async def connect(self, websocket: WebSocket, user_id: str):
        if user_id not in self.active_connections:
            await websocket.accept()
            self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str, room_serv:RoomService):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        # Clean up room memberships
        for room_type in room_serv.rooms:
            for room_id in room_serv.rooms[room_type]:
                if user_id in room_serv.rooms[room_type][room_id]:
                    if room_serv.rooms[room_type][room_id]['clients']:
                        room_serv.rooms[room_type][room_id]['clients'].discard(user_id)

    async def join_room(self, user_id: str, room_type: str, room_id: str, room_serv:RoomService):
        if user_id not in room_serv.rooms[room_type][room_id]['clients']:
            room_serv.rooms[room_type][room_id]['clients'].add(user_id)
            logger.info(f"User {user_id} joined {room_type}/{room_id}. Current members: {room_serv.rooms[room_type][room_id]}")

    async def leave_room(self, user_id: str, room_type: str, room_id: str, room_serv:RoomService):
        if room_type in room_serv.rooms and room_id in room_serv.rooms[room_type]:
            logger.debug(type(room_serv.rooms[room_type][room_id]['clients']))
            logger.debug(type(user_id))
            if room_serv.rooms[room_type][room_id]['clients']:
                room_serv.rooms[room_type][room_id]['clients'].discard(user_id)
                logger.info(f"User {user_id} left {room_type}/{room_id}")

        logger.info(room_serv.rooms)

    async def send_personal_message(self, message: str, user_id: str, room_service:RoomService):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {str(e)}")
                await self.disconnect(user_id, room_service)

    async def broadcast_to_room(self, message: str, room_type: str, room_id: str, room_serv:RoomService, exclude_user: Optional[str] = None):
        logger.debug('In broadcast logic')
        logger.debug(room_serv.rooms)
        if room_type in room_serv.rooms and room_id in room_serv.rooms[room_type]:
            for user_id in list(room_serv.rooms[room_type][room_id]['clients']):
                if user_id in self.active_connections and user_id != exclude_user:
                    try:
                        logger.debug('Actual sending text')
                        await self.active_connections[user_id].send_text(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {user_id}: {str(e)}")
                        await self.disconnect(user_id, room_serv)

    async def broadcast_to_direct(self, message: str, actor_id: str, recipient_id: str, room_serv:RoomService, exclude_user: Optional[str] = None):
        logger.debug(room_serv.rooms)
        if actor_id in room_serv.directs and recipient_id == room_serv.directs[actor_id]['recipient_id']:
            for user_id in list(room_serv.directs[actor_id]['recipient_id']):
                if user_id in self.active_connections and user_id != exclude_user:
                    try:
                        logger.debug('Actual sending text')
                        await self.active_connections[user_id].send_text(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {user_id}: {str(e)}")
                        await self.disconnect(user_id, room_serv)