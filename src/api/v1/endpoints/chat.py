from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import uuid
from datetime import datetime
import logging

from src.core.services.chat.chat_manager import manager
 

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/trash/{room_id}")
async def trash_endpoint(websocket: WebSocket, room_id:str, client_id:str):
    await manager.connect(websocket, client_id)
    
    try:
        await manager.join_room(client_id, room_id)
        await manager.send_personal_message(
            f"Connected to room {room_id} as {client_id[:8]}", 
            client_id
        )
        
        while True:
            data = await websocket.receive_text()
            logger.debug(data)
            await manager.broadcast_to_room(
                f"User {client_id[:8]}: {data}", 
                room_id,
                client_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast_to_room(
            f"User {client_id[:8]} left the chat", 
            room_id,
            client_id
        )