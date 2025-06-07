from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.requests import Request
import logging
import json

from src.core.services.database.orm.chat_orm import save_message
from src.core.dependencies.db_injection import DBDI
from src.core.services.chat.chat_manager import manager
from src.utils.prepared_response import prepare_template 
from src.core.config.config import templates, settings
from src.core.dependencies.auth_injection import AuthDependency


router = APIRouter(prefix=settings.prefix.api_data.prefix, tags=['api'])
logger = logging.getLogger(__name__)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str,
    session: DBDI
):
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            raw_message = await websocket.receive()
            
            if raw_message.get("type") == "websocket.receive":
                if "text" in raw_message:
                    try:
                        data = json.loads(raw_message["text"])
                        await handle_ws_message(user_id, session, data)
                    except json.JSONDecodeError:
                        await manager.send_personal_message(
                            json.dumps({
                                "error": "Invalid JSON format",
                                "your_message": raw_message["text"]
                            }),
                            user_id
                        )
                    
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        await manager.disconnect(user_id)

async def handle_ws_message(user_id: str, session: DBDI, data: dict):
    """Handle different types of WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "join_room":
        # Handle joining a room
        room_id = data.get("room_id")
        if not room_id:
            return await manager.send_personal_message(
                json.dumps({"error": "room_id is required"}), 
                user_id
            )
        await manager.join_room(user_id, room_id)
        
    elif message_type == "leave_room":
        # Handle leaving a room
        room_id = data.get("room_id")
        if not room_id:
            return await manager.send_personal_message(
                json.dumps({"error": "room_id is required"}), 
                user_id
            )
        await manager.leave_room(user_id, room_id)
        
    elif message_type == "chat_message":
        # Handle chat messages
        room_id = data.get("room_id")
        content = data.get("content")
        
        if not all([room_id, content]):
            return await manager.send_personal_message(
                json.dumps({"error": "room_id and content are required"}), 
                user_id
            )
            
        # Save to database
        message = await save_message(session, room_id, user_id, content)
        
        # Broadcast to room
        await manager.broadcast_to_room(
            json.dumps({
                "type": "chat_message",
                "room_id": room_id,
                "user_id": user_id,
                "content": content,
                "timestamp": message.created_at.isoformat()
            }),
            room_id
        )
        
    else:
        await manager.send_personal_message(
            json.dumps({"error": "Unknown message type"}), 
            user_id
        )

@router.get('/chat_room')
async def index(
    request:Request,
    auth_service: AuthDependency
    ):
    user_data = await auth_service.gather_user_data(request=request)

    logger.debug(user_data)

    prepared_data = {
        "title":"Chat-page"
        }
    
    add_data = {
            "request":request,
            "settings":settings,
            "user_id":user_data.get('sub')
            }

    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
        )

    response = templates.TemplateResponse('chat.html', template_response_body_data)
    return response