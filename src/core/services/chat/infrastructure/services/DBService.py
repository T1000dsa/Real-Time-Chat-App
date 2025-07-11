from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

from src.core.schemas.message_shema import MessageSchema, MessabeSchemaBase, DirectMessage, DirectScheme
from src.core.services.chat.domain.interfaces.DBRepo import DBRepo
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager
from src.core.services.database.models.chat import MessageModel, DirectModel
from src.core.services.database.orm.chat_orm import(
    select_messages,
    select_messages_direct,
    save_message,
    save_message_direct
)
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)

class DBService(DBRepo):
    @time_checker
    async def save_message_db(self, session:AsyncSession, message:str, room_type:str, room_id:str, sender_id:str):
        message_data = MessageSchema(user=sender_id, room_type=room_type, room_id=room_id, message=message)
        await save_message(session, message_data)

    @time_checker
    async def save_message_db_direct(self, session:AsyncSession, message:str, actor_id:str, recipient_id:str):
        message_data = DirectScheme(actor_id=actor_id, recipient_id=recipient_id, message=message)
        await save_message_direct(session, message_data)

    @time_checker
    async def receive_messages(self, session:AsyncSession, room_type:str, room_id:str, sender_id:str):
        message_data = MessabeSchemaBase(user=sender_id,room_type=room_type, room_id=room_id)
        return await select_messages(session, message_data)
    
    @time_checker
    async def receive_messages_direct(self, session:AsyncSession, actor_id:str, recipient_id:str):
        message_data = DirectMessage(actor_id=actor_id, recipient_id=recipient_id)
        return await select_messages_direct(session, message_data)
    
    async def load_message_history(
            self, 
            session:AsyncSession,
            connection_manager: ConnectionManager, 
            room_service: RoomService,  
            room_type: str, 
            room_id: str, 
            user_id: str, 
            limit: int = 50
            ):
        # Get from in-memory first
        room = room_service.rooms.get(room_type, {}).get(room_id)
        messages_room = room.get('messages')
        logger.debug(f"{room} {messages_room}")

        
        messages:list[MessageModel] = await self.receive_messages(
                session=session,
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
                await connection_manager.send_personal_message(
                        json.dumps(message_data),
                        user_id,
                        room_service
                    )
                
    async def load_message_history_direct(
            self, 
            session:AsyncSession,
            connection_manager: ConnectionManager, 
            room_service: RoomService,   
            recipient_id: str, 
            actor_id: str, 
            limit: int = 50
            ):
        # Get from in-memory first
        room = room_service.directs.get(actor_id, {})
        messages_room = room.get('messages')
        logger.debug(f"{room} {messages_room}")

        
        messages:list[DirectModel] = await self.receive_messages_direct(
                session=session,
                actor_id=actor_id,
                recipient_id=recipient_id
            )
            
        for msg in messages:
            logger.debug(f"{recipient_id=} {actor_id=}")
            logger.debug(f"{msg.recipient_id=} {msg.actor_id=}")
            if recipient_id == msg.recipient_id or recipient_id == msg.actor_id:
                message_data = {
                        "id": str(msg.id),
                        "type": "historical",
                        "sender_id": msg.actor_id,
                        "content": msg.message,
                        "timestamp": msg.created_at.isoformat()
                    }
                await connection_manager.send_personal_message(
                        json.dumps(message_data),
                        actor_id,
                        room_service
                    )