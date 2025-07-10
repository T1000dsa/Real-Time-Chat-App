import json
import logging
from datetime import datetime
from typing import Dict
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.chat.domain.interfaces.MessageRepo import MessageRepository
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.DBService import DBService


logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, connection_manager:ConnectionManager):
        self.connection_manager = connection_manager

    async def process_message(
            self, 
            session:AsyncSession, 
            DBService:DBService, 
            room_service: RoomService, 
            message_data: Dict, 
            room_type: str, 
            room_id: str, 
            user_id: str,
            user_login: str
            ):
        try:
            # Create full message object
            full_message = {
                "id": str(uuid.uuid4()),
                "type": "message",
                "sender_id": user_id,
                "sender": message_data.get('sender', 'Anonymous'),
                "content": message_data.get('content'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to database
            await DBService.save_message_db(
                session,
                message=f"{user_login}: {full_message['content']}",
                room_type=room_type,
                room_id=room_id,
                sender_id=user_id
            )
            
            # Add to room's in-memory history
            await room_service.add_message_to_room(room_type, room_id, full_message)
            
            # Broadcast to room
            await self.connection_manager.broadcast_to_room(
                message=json.dumps(full_message),
                room_type=room_type,
                room_id=room_id,
                room_serv=room_service,
                exclude_user=user_id
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            raise

    async def process_message_direct(
            self, 
            session:AsyncSession, 
            DBService:DBService, 
            room_service: RoomService, 
            message_data: Dict, 
            actor_id:str,
            recepient:str,
            ):
        try:
            # Create full message object
            full_message = {
                "id": str(uuid.uuid4()),
                "type": "message",
                "sender_id": actor_id,
                "sender": message_data.get('actor_id', 'Anonymous'),
                "content": message_data.get('content'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to database
            await DBService.save_message_db(
                session,
                message=f"{actor_id}: {full_message['content']}",
                room_type='direct',
                room_id=recepient,
                sender_id=actor_id
            )
            
            # Add to room's in-memory history
            #await room_service.add_message_to_room(room_type, room_id, full_message)
            
            # Broadcast to room
            await self.connection_manager.broadcast_to_room(
                message=json.dumps(full_message),
                room_type='direct',
                room_id=recepient,
                room_serv=room_service,
                exclude_user=actor_id
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            raise