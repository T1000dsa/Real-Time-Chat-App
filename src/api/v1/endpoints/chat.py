from fastapi import WebSocket, WebSocketDisconnect, APIRouter,Request, Query, Form
from fastapi.responses import RedirectResponse
from typing import Optional
import logging
import json

from src.core.config.config import templates
from src.utils.prepared_response import prepare_template 
from src.core.dependencies.db_injection import db_helper
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER, create_auth_provider
from src.core.dependencies.chat_injection import HTTPChantManagerDI, WSChantManagerDI


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/rooms')
async def rooms_connection(
    request: Request,
    user:GET_CURRENT_ACTIVE_USER,
    chat_manager:HTTPChantManagerDI
):
    logger.debug(chat_manager._room_serv)

    async with db_helper.async_session() as db_session:
        auth = create_auth_provider(db_session)
        active_users = await auth._user.get_all_active_users(auth.session)
        private_rooms = await chat_manager._room_serv.get_available_rooms()

        logger.debug(private_rooms)

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

@router.get('/chat/{room_type}/{room_name}')
async def general_chats_room(
    request: Request, 
    user: GET_CURRENT_ACTIVE_USER, 
    room_type:str, 
    room_name: str,
    chat_manager:HTTPChantManagerDI
):
    logger.debug(chat_manager._room_serv.rooms)
    # Validate room exists
    if room_type not in chat_manager._room_serv.rooms or room_name not in chat_manager._room_serv.rooms[room_type]:
        if room_type == 'private':
            return RedirectResponse(url="/rooms", status_code=303)
        

    if chat_manager._room_serv.rooms.get(room_type) is None:
        await chat_manager._room_serv.create_room(room_type, room_name)


    logger.debug(chat_manager._room_serv.rooms)


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

@router.websocket("/ws/chat/{room_type}/{room_name}")
async def chat_endpoint(
    websocket: WebSocket,
    chat_manager: WSChantManagerDI,
    room_type: str,
    room_name: str,
    user_id: str = Query(...),
    user_login: str = Query(...),
    password: str = Query(None)
):
    # Connect to WebSocket
    logger.debug(f'In websocket: {chat_manager._room_serv.rooms}')
    await chat_manager._msg_repo.connection_manager.connect(websocket, user_id)
    
    try:
        # Validate and join room
        """if not await room_service.validate_room_access(room_type, room_id, password):
            logger.debug('Validate room false')
            await websocket.close(code=4003, reason="Invalid password or room")
            return"""
        
        logger.debug(f'{user_id} tries to join {room_name}')
        await chat_manager._msg_repo.connection_manager.join_room(user_id, room_type, room_name, chat_manager._room_serv)
        logger.debug(chat_manager._room_serv.rooms)
        
        # Load message history
        await chat_manager._db_service.load_message_history(
            chat_manager.session, 
            chat_manager._msg_repo.connection_manager,
            chat_manager._room_serv, 
            room_type, 
            room_name, 
            user_id
        )
        
        # Main message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add sender info to message
            message['sender'] = user_login
            message['sender_id'] = user_id
            
            await chat_manager._msg_repo.process_message(
                chat_manager.session, 
                chat_manager._db_service,
                chat_manager._room_serv, 
                message,
                room_type,
                room_name,
                user_id,
                user_login
            )
                
    except WebSocketDisconnect:
        logger.info(f"User {user_login} disconnected")
    finally:
        logger.info(f"In finally body")
        await chat_manager._msg_repo.connection_manager.leave_room(user_id, room_type, room_name, chat_manager._room_serv)
        await chat_manager._msg_repo.connection_manager.disconnect(user_id, chat_manager._room_serv)


@router.post("/create_room")
async def create_protected_room(
    request: Request,
    user: GET_CURRENT_ACTIVE_USER,
    chat_manager:HTTPChantManagerDI,
    name: str = Form(...),
    password: Optional[str] = Form(None),
    room_type: str = Form('private')  # Default to private
):
    logger.debug(f'{name=} {password=}')
    # Create the room and get its ID
    room_id = await chat_manager._room_serv.create_room(room_type, name, password)
    
    # Join the creator to the room
    success = await chat_manager._msg_repo.connection_manager.join_room(
        chat_manager._room_serv,
        user_id=str(user.id),
        room_type=room_type,
        room_id=room_id,
        password=password,
        room_serv=chat_manager._room_serv
    )

    response = RedirectResponse(
        url=f"/chat/{room_type}/{room_id}",
        status_code=303
    )

    chat_manager._room_serv.rooms[f'room_password_{room_id}'] = password
    chat_manager._room_serv.rooms[f'room_id'] = room_id
    
    if not success:
        # Handle join failure
        return RedirectResponse(
            url="/rooms",
            status_code=303
        )
    
    return response