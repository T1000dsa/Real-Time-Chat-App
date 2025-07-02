import json
import logging
from datetime import datetime
from typing import Dict, Optional

from src.core.dependencies.auth_injection import create_auth_provider
from src.core.dependencies.db_injection import db_helper
from src.core.services.database.models.chat import MessageModel
from src.core.services.chat.domain.interfaces.MessageRepo import MessageRepository
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.utils.time_check import time_checker
from src.core.services.cache.redis import manager as redis_manager
from src.core.config.config import settings


logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def process_message(self, room_service: RoomService, message_data: Dict, room_type: str, room_id: str, sender_id: str):
        try:
            # Save to database
            message_id = await self.save_message_to_db(
                content=message_data.get('content'),
                room_type=room_type,
                room_id=room_id,
                sender_id=sender_id
            )
            
            # Add to room's in-memory history
            full_message = {
                "id": message_id,
                "type": "message",
                "sender_id": sender_id,
                "content": message_data.get('content'),
                "timestamp": datetime.now().isoformat()
            }
            room_service.rooms[room_type] = {room_id:{'messages':full_message}}

            
            # Broadcast to room
            await self.connection_manager.broadcast_to_room(
                message=json.dumps(full_message),
                room_type=room_type,
                room_id=room_id,
                exclude_user=sender_id
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")

    async def save_message_to_db(self, content: str, room_type: str, room_id: str, sender_id: str) -> str:
        async with db_helper.async_session() as session:
            auth = create_auth_provider(session)
            user = await auth._repo.get_user_for_auth_by_id(auth.session, int(sender_id))
            await auth._db.save_message_db(
                auth.session, 
                f"{user.login}: {content}",
                room_type,
                room_id,
                sender_id
                )


    async def load_message_history(self, room_service: RoomService,  room_type: str, room_id: str, user_id: str, limit: int = 50):
        # Get from in-memory first
        room = room_service.rooms.get(room_type, {}).get(room_id)
        logger.debug(room)

        if room and room['messages']:
            for message in room['messages']:
                await self.connection_manager.send_personal_message(
                    json.dumps(message),
                    user_id
                )
            return
        
        # Fallback to database
        async with db_helper.async_session() as session:
            auth = create_auth_provider(session)
            messages:list[MessageModel] = await auth._db.receive_messages(
                auth.session,
                room_id=room_id,
                room_type=room_type,
                sender_id=user_id
            )
            
            for msg in messages:
                if room_type == msg.room_type and room_id == msg.room_id:
                    message_data = {
                        "id": str(msg.id),
                        "type": "historical",
                        "sender_id": msg.user_id,
                        "content": msg.message,
                        "timestamp": msg.created_at.isoformat()
                    }
                    await self.connection_manager.send_personal_message(
                        json.dumps(message_data),
                        user_id
                    )
                    room_service.rooms.get(room_type, {}).get(room_id)
                    room_service.rooms[room_type] = {room_id:{'messages':message_data}}