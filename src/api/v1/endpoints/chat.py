from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, status
import logging
import json

from src.core.config.config import templates
from src.core.services.chat.chat_manager import manager
from src.core.config.config import settings
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER
from src.utils.prepared_response import prepare_template 

router = APIRouter(prefix=settings.prefix.api_data.prefix)
logger = logging.getLogger(__name__)


@router.get("/chat_room")
async def get_chat_page(request: Request, user:GET_CURRENT_ACTIVE_USER):
    # Generate a random client ID or use the authenticated user's ID
    prepared_data = {
        "title":"Main page"
        }
    
    add_data = {
            "request":request,
            "client_id": user.id,
            "websocket_url": f"ws://{request.url.hostname}/ws/{user.id}"
            }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
        )
    
    return templates.TemplateResponse('chat.html', template_response_body_data)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: int,
    current_user: GET_CURRENT_ACTIVE_USER
):
    logger.info(f"WebSocket connection attempt from client {client_id}")

    try:
        if current_user.id != client_id:
            logger.error(f"Authorization failed for client {client_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as auth_error:
        logger.error(f"Authentication error: {str(auth_error)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    
    if current_user.id != client_id:
        logger.warning(f"Client ID mismatch: {current_user.id} != {client_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        await manager.connect(websocket, client_id, {"username": current_user.login})
        logger.info(f"Client {client_id} ({current_user.login}) connected successfully")
        
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received message from {client_id}: {data}")
                await manager.broadcast(
                    f"{current_user.login}: {data}",
                    client_id
                )
            except WebSocketDisconnect as e:
                logger.info(f"Client {client_id} disconnected: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "An error occurred processing your message"
                }))
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        manager.disconnect(websocket, client_id)
        await manager.notify_webhook(
            "disconnection",
            client_id,
            {"status": "disconnected", "username": current_user.login}
        )
        await manager.broadcast(
            f"System: {current_user.login} left the chat",
            client_id
        )
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {str(e)}")
        manager.disconnect(websocket, client_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@router.post("/webhook")
async def handle_webhook(request: Request, payload: dict):
    event_type = payload.get("event")
    client_id = payload.get("client_id")
    
    if event_type == "user_update":
        user_data = payload.get("data")
        logger.info(f"Received user update for {client_id}: {user_data}")

        try:
        
            if client_id in manager.active_connections:
                await manager.active_connections[client_id].send_text(
                    json.dumps({
                        "type": "system",
                        "message": f"Your profile was updated: {user_data}"
                    })
                )
        except Exception as err:
            logger.error(f'Something wrong: {err}')
        
    # You could return a template response if needed
    if payload.get("return_html"):
        prepared_data = {
            "title":"Main page"
            }
        
        add_data = {
                    "status": "success",
                    "request": request,
                    "event": event_type,
                    "client_id": client_id
                    }
            
        template_response_body_data = await prepare_template(
                data=prepared_data,
                additional_data=add_data
                )
        
        return templates.TemplateResponse('chat.html', template_response_body_data)

    
    return {"status": "received"}

@router.get("/connections")
async def list_connections(request:Request):
    prepared_data = {
            "title":"Chat page"
            }
        
    add_data = {
                "active_connections": list(manager.active_connections.keys()),
                "user_info": manager.user_info,
                "request":request
                }
        
    template_response_body_data = await prepare_template(
            data=prepared_data,
            additional_data=add_data
            )
        
    return templates.TemplateResponse('chat.html', template_response_body_data)

@router.get("/test-websocket")
async def test_websocket(request: Request):
    """Test endpoint to verify template rendering"""
    prepared_data = {
            "title":"Chat page"
            }
        
    add_data = {
                "request": request,
                "title": "WebSocket Test",
                "client_id": 999,
                "websocket_url": f"ws://{request.url.hostname}/ws/999"
                }
        
    template_response_body_data = await prepare_template(
            data=prepared_data,
            additional_data=add_data
            )
        
    return templates.TemplateResponse('chat.html', template_response_body_data)

@router.get("/messages")
async def get_messages():
    return manager.messages