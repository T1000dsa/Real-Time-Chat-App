from fastapi import WebSocket, WebSocketDisconnect, APIRouter,Request, Query
import json
import logging

from src.core.config.config import templates
from src.utils.prepared_response import prepare_template 
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER, AuthDependency
from src.core.dependencies.chat_injection import HTTPChantManagerDI, WSChantManagerDI


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/direct-message-with-{username}')
async def direct_message_endpoint(
    request:Request,
    chat_manager:HTTPChantManagerDI,
    user:GET_CURRENT_ACTIVE_USER,
    username:str,
    auth:AuthDependency
):
    logger.debug(f"{username} - recipient, {user.login} - actor")
    recipient_user = await auth._user._repo.get_user_for_auth(auth.session, username)

    prepared_data = {
            "title": f"Direct-room with"
        }

    add_date = {
            'user':user,
            'recipient_user':recipient_user,
            'recipient':username,
            'actor':user.id
        }

    template_response_body_data = await prepare_template(
            data=prepared_data,
            additional_data=add_date
        )
    
    return templates.TemplateResponse(
        request=request,
        name='direct_msg.html',
        context=template_response_body_data
    )

@router.websocket("/ws/direct-message-with-{username}")
async def direct_message_endpoint_websocket(
    websocket: WebSocket,
    chat_manager:WSChantManagerDI,
    recipient_id: str = Query(...),
    actor_id: str = Query(...),
):
    logger.debug(f"{recipient_id=} {actor_id=}")

    await chat_manager._msg_repo.connection_manager.connect(websocket, actor_id)

    try:
        
        logger.debug(f'{actor_id} tries to join {recipient_id}')
        await chat_manager._room_serv.create_direct(actor_id, recipient_id)
        
        
        # Main message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add sender info to message
            message['recipient_id'] = recipient_id
            message['actor_id'] = actor_id
            
            await chat_manager._msg_repo.process_message_direct(
                chat_manager.session, 
                chat_manager._db_service,
                chat_manager._room_serv, 
                message,
                actor_id,
                recipient_id
            )
                
    except WebSocketDisconnect:
        logger.info(f"User {actor_id} disconnected")
    finally:
        logger.info(f"In finally body")
        await chat_manager._room_serv.leave_direct(actor_id, recipient_id)
        await chat_manager._msg_repo.connection_manager.disconnect(actor_id, chat_manager._room_serv)