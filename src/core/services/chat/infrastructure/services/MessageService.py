import json
import logging
from collections import defaultdict

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

class MessageService(MessageRepository):
    def __init__(self, connection_manager:ConnectionManager):
        self.connection_manager = connection_manager
        self.message_history = defaultdict(list)  # room_id: list[messages]

    @time_checker
    async def process_message(self, message: str, room_id: str, sender_id: str):
        try:
            message_dict = json.loads(message)
            
            if message_dict.get('type') == 'message':
                # Save to database
                async with db_helper.async_session() as db_session:
                    auth = create_auth_provider(db_session)
                    user_data = await auth._repo.get_user_for_auth_by_id(auth.session, int(sender_id))
                    formatted_message = f'{user_data.login}: {message_dict.get("content")}'
                    await self.save_message(formatted_message, room_id, sender_id)
                    
                    # Broadcast to room
                    await self.broadcast_to_room(message, room_id, sender_id)
                    
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")

    @time_checker
    async def save_message(self, message: str, room_type:str, room_id: str, sender_id: str):
        logger.debug('Trying to save message...')
        async with db_helper.async_session() as db_session:
            auth = create_auth_provider(db_session)
            await auth._db.save_message_db(auth.session, message, room_type, room_id, sender_id)
    @time_checker
    async def broadcast_to_room(self, room_service:RoomService, message: str, room_type:str, room_id: str, sender_id: str):
        if room_type in room_service.rooms and room_id in room_service.rooms[room_type]:
            room = room_service.rooms[room_type][room_id]
            disconnected_clients = []
            
            # Only save user messages, not system messages
            try:
                message_dict = json.loads(message)
                logger.debug(message_dict) 
                if message_dict.get('type') == 'message':  # Only save actual user messages
                    async with db_helper.async_session() as db_session:
                        auth = create_auth_provider(db_session)
                        user_data = await auth._repo.get_user_for_auth_by_id(auth.session, int(sender_id))
                        await self.save_message(
                            f'{user_data.login}: {message_dict.get("content")}', 
                            room_type,
                            room_id, 
                            sender_id
                        )
            except Exception as e:
                logger.error(f"Failed to save message: {str(e)}")
            
            # Broadcast to all clients except sender
            for user_id in list(room['clients']):
                if user_id != sender_id:
                    try:
                        await self.connection_manager.send_personal_message(message, user_id)
                    except:
                        disconnected_clients.append(user_id)
            
            # Clean up disconnected clients
            for user_id in disconnected_clients:
                await self.connection_manager.leave_room(user_id, room_type, room_id)
                self.connection_manager.disconnect(user_id)
    @time_checker
    async def load_history(self, room_id: str, client_id: str, room_type:str):
        async with db_helper.async_session() as db_session:
            auth = create_auth_provider(db_session)
            messages:list[MessageModel] = await auth._db.receive_messages(auth.session, room_id, client_id)
            
            unique_messages = set()
            for msg in messages:
                if msg.message not in unique_messages:
                    unique_messages.add(msg.message)
                    try:
                        if room_id == msg.room_id and room_type == msg.room_type:
                            user_data = await auth._repo.get_user_for_auth_by_id(auth.session, int(msg.user_id))
                            cache_data:bytes = await redis_manager.redis.get(msg.id)
                            logger.debug(f"cached data: {cache_data} {type(cache_data)}")
                            if cache_data:
                                await self.connection_manager.send_personal_message(cache_data.decode(), client_id)

                            else:
                                message_data = json.dumps({
                                    "id": str(msg.id),
                                    "type": "historical",
                                    "sender_id": msg.user_id,
                                    "sender": user_data.login,
                                    "content": msg.message,
                                    "timestamp": msg.created_at.isoformat()
                                })
                                logger.debug(f"message_data: {cache_data}")
                                await redis_manager.redis.set(msg.id, message_data, ex=settings.redis.cache_time)
                                await self.connection_manager.send_personal_message(message_data, client_id)
                    except Exception as e:
                        logger.error(f"Error sending historical message: {str(e)}")