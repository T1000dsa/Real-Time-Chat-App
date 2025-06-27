from fastapi import Depends
from typing import Annotated

from src.core.services.chat.infrastructure.services.ChatManager import ChatManager
from src.core.services.chat.infrastructure.services.MessageService import MessageService
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager


def get_meessage_connection_manager() -> ConnectionManager:
    return ConnectionManager()

def get_message_service(
        conn_manager = Depends(get_meessage_connection_manager)
        ) -> MessageService:
    
    message_service = MessageService(connection_manager=conn_manager)
    return message_service

def get_room_service() -> RoomService:
    return RoomService()

def get_chat_manager(
        message_service = Depends(get_message_service),
        room_service = Depends(get_room_service)

        ) -> ChatManager:
    return ChatManager(message_repo=message_service, room_service=room_service)


ChantManagerDI = Annotated[ChatManager, Depends(get_chat_manager)]