from fastapi import WebSocket, WebSocketDisconnect, APIRouter,Request, Query, Form
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import datetime 
import logging
import uuid
import json

from src.core.services.chat.chat_manager import manager
from src.core.config.config import templates
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER
from src.utils.prepared_response import prepare_template 
from src.core.services.cache.redis import manager as redis_manager
from src.core.config.config import settings


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/rooms')
async def rooms_connection(
    request: Request,
):
    rooms = await manager.get_private_rooms()
    prepared_data = {
        "title": f"Rooms page"
    }

    add_date = {
        'other_rooms':rooms
    }

    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_date
    )
    
    return templates.TemplateResponse(
        request=request,
        name='rooms.html',
        context=template_response_body_data
    )

@router.get('/chat/{room_type}/{room_id}')
async def general_chats_room(
    request: Request, 
    user: GET_CURRENT_ACTIVE_USER, 
    room_type:str, 
    room_id: str
):
    logger.debug(f"{room_type=} {room_id=}")
    #logger.debug(manager.rooms)
    # Validate room exists
    if room_type not in manager.rooms or room_id not in manager.rooms[room_type]:
        if room_type == 'private':
            return RedirectResponse(url="/rooms", status_code=303)
        # For general rooms, create automatically
        manager.rooms[room_type][room_id] = {
            'name': f"{room_type} {room_id}",
            'password': None,
            'clients': set()
        }

    prepared_data = {
        "title": f"{room_type.title()} chat"
    }

    add_data = {
        "user":user
    }
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )
    return templates.TemplateResponse(
        request=request,
        name='chat.html',
        context=template_response_body_data
    )

@router.websocket("/ws/chat/{room_type}/{room_id}")
async def chat_endpoint(
    websocket: WebSocket,
    room_type: str,
    room_id: str,
    user_id: str = Query(...),
    user_login: str = Query(...),
    password: str = Query(None),
):
    if password is None:
        password = manager.protected_cons.get(f'room_password_{room_id}', None)


    logger.debug(f"Current rooms structure: {manager.rooms}")
    
    # Initialize room if it doesn't exist
    if room_type not in manager.rooms or room_id not in manager.rooms[room_type]:
        if room_type == 'private':
            await websocket.close(code=4004, reason="Room does not exist")
            return
        # For general rooms, create automatically
        manager.rooms[room_type][room_id] = {
            'name': f"{room_type} {room_id}",
            'password': None,
            'clients': set()
        }
    await manager.connect(websocket, user_id)
    logger.info(f'User {user_login} connected to: {room_type}/{room_id}')
    
    try:
        # Validate room access with password if needed
        if not await manager.join_room(
            user_id=user_id,
            room_type=room_type,
            room_id=room_id,
            password=password
        ):
            await websocket.close(code=4003, reason="Invalid password or room")
            return
        
        # Send join notification
        await manager.broadcast_to_room(
            json.dumps({
                "type": "system",
                "content": f"{user_login} joined the chat"
            }),
            room_type,
            room_id,
            user_id
        )
        
        # Main message loop
        while True:
            data = await websocket.receive_text()
            
            # Parse message with error handling
            try:
                msg = json.loads(data)
                if not isinstance(msg, dict):
                    raise ValueError("Invalid message format")
                    
                # Construct standardized message
                message = {
                    "id": str(uuid.uuid4()),
                    "type": "message",
                    "sender_id": user_id,
                    "sender": user_login,
                    "content": msg.get("content", ""),
                    "timestamp": datetime.now().isoformat()
                }
                
                await manager.broadcast_to_room(
                    json.dumps(message),
                    room_type,
                    room_id,
                    user_id
                )
                
            except Exception as e:
                logger.debug(e)
                error_msg = {
                    "type": "error",
                    "content": f"Invalid message format: {str(e)}"
                }
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect as e:
        logger.info(f"User {user_login} disconnected: {str(e)}")
    finally:
        await manager.leave_room(user_id, room_type, room_id)
        # Send leave notification
        await manager.broadcast_to_room(
            json.dumps({
                "type": "system",
                "content": f"{user_login} left the chat"
            }),
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
    room_type: str = Form('private')  # Default to private
):
    logger.debug(f'{name=} {password=}')
    # Create the room and get its ID
    room_id = await manager.create_protected_room(name, password)
    
    # Join the creator to the room
    success = await manager.join_room(
        user_id=str(user.id),
        room_type=room_type,
        room_id=room_id,
        password=password  # Pass the same password used for creation
    )

    response = RedirectResponse(
        url=f"/chat/{room_type}/{room_id}",
        status_code=303
    )

    #request.session["room_password"] = password
    #request.session["room_id"] = room_id  # Good practice to store room_id too
    manager.protected_cons[f'room_password_{room_id}'] = password
    manager.protected_cons[f'room_id'] = room_id
    
    if not success:
        # Handle join failure
        return RedirectResponse(
            url="/rooms",
            status_code=303
        )
    
    return response