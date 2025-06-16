from fastapi import WebSocket, WebSocketDisconnect, APIRouter,Request, Query, Form
from fastapi.responses import RedirectResponse
import logging
import uuid
from typing import Optional
import json

from src.core.services.chat.chat_manager import manager
from src.core.config.config import templates
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER
from src.utils.prepared_response import prepare_template 


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/rooms')
async def rooms_connection(
    request: Request,
):
    prepared_data = {
        "title": f"Rooms page"
    }

    
    template_response_body_data = await prepare_template(
        data=prepared_data,
    )
    
    return templates.TemplateResponse(
        request=request,
        name='rooms.html',
        context=template_response_body_data
    )

@router.websocket("/ws/chat/{room_type}/{room_id}")
async def chat_endpoint(
    websocket: WebSocket,
    room_type: str,
    room_id: str = "main",  # Default value
    user_id: str = Query(...),
    user_login: str = Query(...)
):
    logger.debug('websocket')

    await manager.connect(websocket, user_id)
    await manager.join_room(user_id, room_type, room_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # Broadcast with sender info and message ID
                await manager.broadcast_to_room(
                    json.dumps({
                        "id": message_data.get("id", str(uuid.uuid4())),
                        "sender": user_login,
                        "content": message_data["content"]
                    }),
                    room_type,
                    room_id,
                    user_id
                )
            except json.JSONDecodeError:
                # Fallback for plain text
                await manager.broadcast_to_room(
                    f"{user_login}: {data}",
                    room_type,
                    room_id,
                    user_id
                )
    
    except WebSocketDisconnect:
        await manager.leave_room(user_id, room_type, room_id)
        await manager.broadcast_to_room(
            f"System: {user_login} left the chat",
            room_type,
            room_id,
            user_id
        )


@router.post("/create_room")
async def create_protected_room(
    request: Request,
    user: GET_CURRENT_ACTIVE_USER,
    name: str = Form(...),
    password: Optional[str] = Form(None),

):
    room_id = str(uuid.uuid4())
    manager.create_protected_room(room_id, name, password)
    return RedirectResponse(
        url=f"/chat/private/{room_id}",
        status_code=303
    )


@router.get("/rooms_list")
async def list_rooms(user: GET_CURRENT_ACTIVE_USER):
    return {
           "public_rooms": manager.get_public_rooms(),
           "user_rooms": manager.get_user_rooms(str(user.id))
       }

@router.websocket("/ws/chat/{room_type}/{room_id}")
async def chat_endpoint(
    websocket: WebSocket,
    room_type: str,
    room_id: str = None,
    user_id: str = Query(...),
    user_login: str = Query(...)
):
    
    try:
        # Connect and join room
        await manager.connect(websocket, user_id)
        await manager.join_room(user_id, room_type, room_id)
        
        # Notify room
        await manager.broadcast_to_room(
            f"User {user_login} joined the {room_type} room {room_id}",
            room_type,
            room_id,
            user_id
        )
        
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_to_room(
                f"{user_login}: {data}",
                room_type,
                room_id,
                user_id
            )
            
    except WebSocketDisconnect:
        await manager.leave_room(user_id, room_type, room_id)
        await manager.broadcast_to_room(
            f"User {user_login} left the {room_type} room {room_id}",
            room_type,
            room_id,
            user_id
        )
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011)