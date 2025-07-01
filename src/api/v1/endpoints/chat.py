from fastapi import WebSocket, WebSocketDisconnect, APIRouter,Request, Query, Form
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import datetime 
import logging
import uuid
import json

from src.core.config.config import templates
from src.utils.prepared_response import prepare_template 

from src.core.dependencies.db_injection import db_helper
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER, create_auth_provider
from src.core.dependencies.chat_injection import ChantManagerDI, get_chat_manager_manual


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/rooms')
async def rooms_connection(
    request: Request,
    user:GET_CURRENT_ACTIVE_USER,
    chat_manager:ChantManagerDI
):
    async with db_helper.async_session() as db_session:
        auth = create_auth_provider(db_session)
        active_users = await auth._user.get_all_active_users(auth.session)
        private_rooms = await chat_manager._room_serv.get_private_rooms()

        prepared_data = {
            "title": f"Rooms page"
        }

        add_date = {
            'other_rooms':private_rooms,
            'users':active_users,
            'user':user
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
    chat_manager:ChantManagerDI,
    room_type:str, 
    room_id: str
):
    logger.debug(f"{room_type=} {room_id=}")
    # Validate room exists
    if room_type not in chat_manager._room_serv.rooms or room_id not in chat_manager._room_serv.rooms[room_type]:
        if room_type == 'private':
            return RedirectResponse(url="/rooms", status_code=303)
        # For general rooms, create automatically
    chat_manager._room_serv.rooms[room_type][room_id] = {
            'name': f"{room_type} {room_id}",
            'password': None,
            'clients': set()
        }
    
    logger.debug(chat_manager._room_serv.rooms[room_type][room_id])

    logger.debug(f"{room_type=} {room_id=}")

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
    logger.debug('general_chats_room success!')
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
    logger.debug('In websocket')
    chat_manager = get_chat_manager_manual()

    if password is None:
        password = chat_manager._room_serv.private_rooms.get(f'room_password_{room_id}', None)


    # Initialize room if it doesn't exist
    if room_type not in chat_manager._room_serv.rooms or room_id not in chat_manager._room_serv.rooms[room_type]:
        if room_type == 'private':
            await websocket.close(code=404, reason="Room does not exist")
            return
        # For general rooms, create automatically
    chat_manager._room_serv.rooms[room_type][room_id] = {
            'name': f"{room_type} {room_id}",
            'password': None,
            'clients': set()
        }
    
     # Also initialize in ConnectionManager's user_rooms
    if room_type not in chat_manager._msg_repo.connection_manager.user_rooms:
        chat_manager._msg_repo.connection_manager.user_rooms[room_type] = {}
        chat_manager._msg_repo.connection_manager.user_rooms[room_type][room_id] = {
            'name': f"{room_type} {room_id}",
            'password': None,
            'clients': set()
        }
    
    logger.debug(chat_manager._room_serv.rooms[room_type][room_id])
    
    await chat_manager._msg_repo.connection_manager.connect(websocket, user_id)
    logger.info(f'User {user_login} connected to: {room_type}/{room_id}')
    
    try:
        # Validate room access with password if needed
        if not await chat_manager._msg_repo.connection_manager.join_room(
            user_id=user_id,
            room_type=room_type,
            room_id=room_id,
            password=password
        ):
            await websocket.close(code=4003, reason="Invalid password or room")
            return
        

        await chat_manager._msg_repo.load_history(
            room_id,
            user_id,
            room_type
        )
        
        # Send join notification
        await chat_manager._msg_repo.broadcast_to_room(
        chat_manager._room_serv,
        json.dumps({
            "id": str(uuid.uuid4()),
            "type": "system",
            "sender": "System",  # Explicit sender
            "content": f"{user_login} joined the chat",
            "timestamp": datetime.now().isoformat()
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
                
                await chat_manager._msg_repo.broadcast_to_room(
                    chat_manager._room_serv,
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
        await chat_manager._msg_repo.connection_manager.leave_room(user_id, room_type, room_id)
        # Send SINGLE leave notification with unique ID
        await chat_manager._msg_repo.broadcast_to_room(
            chat_manager._room_serv,
        json.dumps({
            "id": str(uuid.uuid4()),
            "type": "system",
            "sender": "System",
            "content": f"{user_login} left the chat",
            "timestamp": datetime.now().isoformat()
        }),
        room_type,
        room_id,
        user_id
    )

@router.post("/create_room")
async def create_protected_room(
    request: Request,
    user: GET_CURRENT_ACTIVE_USER,
    chat_manager:ChantManagerDI,
    name: str = Form(...),
    password: Optional[str] = Form(None),
    room_type: str = Form('private')  # Default to private
):
    logger.debug(f'{name=} {password=}')
    # Create the room and get its ID
    room_id = await chat_manager._room_serv.create_room(room_type, name, password)
    
    # Join the creator to the room
    success = await chat_manager._msg_repo.connection_manager.join_room(
        user_id=str(user.id),
        room_type=room_type,
        room_id=room_id,
        password=password
    )

    response = RedirectResponse(
        url=f"/chat/{room_type}/{room_id}",
        status_code=303
    )

    chat_manager._room_serv.private_rooms[f'room_password_{room_id}'] = password
    chat_manager._room_serv.private_rooms[f'room_id'] = room_id
    
    if not success:
        # Handle join failure
        return RedirectResponse(
            url="/rooms",
            status_code=303
        )
    
    return response