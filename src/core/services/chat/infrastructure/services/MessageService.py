import json
from datetime import datetime
from typing import List
import logging
from collections import defaultdict

from src.core.dependencies.auth_injection import create_auth_provider
from src.core.dependencies.db_injection import db_helper
from src.core.services.database.models.chat import MessageModel
from src.core.services.chat.domain.interfaces.MessageRepo import MessageRepository

logger = logging.getLogger(__name__)

class MessageService(MessageRepository):
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.message_history = defaultdict(list)  # room_id: list[messages]

    async def process_message(self, message: str, room_id: str, sender_id: str):
        try:
            message_dict = json.loads(message)
            
            if message_dict.get('type') == 'message':
                # Save to database
                async with db_helper.async_session() as db_session:
                    auth = create_auth_provider(db_session)
                    user_data = await auth._repo.get_user_for_auth_by_id(auth.session, int(sender_id))
                    formatted_message = f'{user_data.login}: {message_dict.get("content")}'
                    await self._save_message(formatted_message, room_id, sender_id)
                    
                    # Broadcast to room
                    await self._broadcast_to_room(message, room_id, sender_id)
                    
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")

    async def _save_message(self, message: str, room_id: str, sender_id: str):
        async with db_helper.async_session() as db_session:
            auth = create_auth_provider(db_session)
            await auth._db.save_message_db(auth.session, message, room_id, sender_id)

    async def _broadcast_to_room(self, message: str, room_id: str, sender_id: str):
        # Get all users in the room
        users_in_room = [
            user_id for user_id, rooms in self.connection_manager.user_rooms.items() 
            if room_id in rooms
        ]
        
        # Send to all except sender
        for user_id in users_in_room:
            if user_id != sender_id:
                await self.connection_manager.send_personal_message(message, user_id)

    async def load_history(self, room_id: str, client_id: str):
        async with db_helper.async_session() as db_session:
            auth = create_auth_provider(db_session)
            messages = await auth._db.receive_messages(auth.session, room_id)
            
            unique_messages = set()
            for msg in messages:
                if msg.message not in unique_messages:
                    unique_messages.add(msg.message)
                    try:
                        user_data = await auth._repo.get_user_for_auth_by_id(auth.session, int(msg.user_id))
                        message_data = json.dumps({
                            "id": str(msg.id),
                            "type": "historical",
                            "sender_id": msg.user_id,
                            "sender": user_data.login,
                            "content": msg.message,
                            "timestamp": msg.created_at.isoformat()
                        })
                        await self.connection_manager.send_personal_message(message_data, client_id)
                    except Exception as e:
                        logger.error(f"Error sending historical message: {str(e)}")