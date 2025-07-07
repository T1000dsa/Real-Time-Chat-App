from fastapi import WebSocket, APIRouter,Request, Query
import logging

from src.core.config.config import templates
from src.utils.prepared_response import prepare_template 
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER
from src.core.dependencies.chat_injection import HTTPChantManagerDI, WSChantManagerDI


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/direct-message-with-{username}')
async def direct_message_endpoint(
    request:Request,
    chat_manager:HTTPChantManagerDI,
    user:GET_CURRENT_ACTIVE_USER,
    username:str
):
    logger.debug(f"{username} - recepient, {user.login} - actor")

    prepared_data = {
            "title": f"Direct-room with {username}"
        }

    add_date = {
            'user':user
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
    recepient_id: str = Query(...),
    actor_id: str = Query(...),
):
    logger.debug(f"{recepient_id=} {actor_id=}")

    chat_manager._msg_repo.connection_manager.connect(websocket, actor_id)
    chat_manager._room_serv.rooms[actor_id][recepient_id] = {
            'name': f"Direct between {actor_id} and {recepient_id}",
            'password': None,
            'clients': set()
        }