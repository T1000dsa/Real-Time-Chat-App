from fastapi import Depends, Request, WebSocket
from typing import Annotated

from src.core.dependencies.db_injection import DBDI
from src.core.services.chat.infrastructure.services.ChatManager import ChatManager
from src.core.services.chat.infrastructure.services.MessageService import MessageService
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager
from src.core.services.chat.infrastructure.services.DBService import DBService


def get_meessage_connection_manager() -> ConnectionManager:
    return ConnectionManager()

def get_room_service() -> RoomService:
    return RoomService()

def get_db_service() -> DBService:
    return DBService()

def get_message_service(
        conn_manager = Depends(get_meessage_connection_manager),
        ) -> MessageService:
    
    message_service = MessageService(connection_manager=conn_manager)
    return message_service

def get_http_room_service(request: Request) -> RoomService:
    """For HTTP routes"""
    return request.app.state.room_service

def get_ws_room_service(websocket: WebSocket) -> RoomService:
    """For WebSocket routes"""
    return websocket.app.state.room_service

def get_chat_manager(
        session:DBDI, 
        message_service = Depends(get_message_service),
        room_service = Depends(get_room_service),
        db_service = Depends(get_db_service)

        ) -> ChatManager:
    return ChatManager(session=session, message_repo=message_service, room_service=room_service, db_service=db_service)

def get_chat_manager_manual(session):
    conn_manager = ConnectionManager()
    room_service = RoomService()
    db_service = DBService()
    message_service = MessageService(connection_manager=conn_manager)

    return ChatManager(session=session, message_repo=message_service, room_service=room_service, db_service=db_service)

ChantManagerDI = Annotated[ChatManager, Depends(get_chat_manager)]