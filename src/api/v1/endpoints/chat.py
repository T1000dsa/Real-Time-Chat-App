from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
import logging
import uuid

from src.core.services.chat.chat_manager import manager, list_mesagges
from src.core.schemas.message_shema import MessageModel, MessageModelRoom, ConnectionTicket, ConnectRequest
from src.core.dependencies.auth_injection import AuthDependency

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, request:Request):
    client_id = await manager.connect(websocket, Request)
    try:
        await manager.join_room(client_id, room_id)
        await manager.send_to_room(room_id, f"Client {client_id[:8]} joined the room")
        
        while True:
            data = await websocket.receive_text()
            await manager.send_to_room(
                room_id, 
                f"Client {client_id[:8]}: {data}",
                sender_id=client_id
            )
            
    except WebSocketDisconnect:
        await manager.leave_room(client_id, room_id)
        await manager.send_to_room(room_id, f"Client {client_id[:8]} left")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        manager.disconnect(client_id)

# HTTP endpoint to push messages to WebSocket clients
@router.post("/send-message")
async def send_message(message: MessageModel):
    """Send message to all connected WebSocket clients"""
    await manager.send_to_client(client_id='server', message=f"HTTP says: {message.message}")
    return {"status": "Message sent", "recipients": len(manager.active_connections)}

@router.get("/messages")
async def get_message_history():
    return {"messages": manager.message_history, "other":list_mesagges}


@router.post("/send-to-room/{room_id}")
async def send_to_room(room_id: str, message: MessageModel):
    """Send message to all clients in a specific room"""
    try:
        await manager.send_to_room(room_id, f"Server: {message.message}")
        return {"status": "Message sent to room", "room": room_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))
    
@router.post("/join-room")
async def join_room(request: Request, room:MessageModelRoom):
    """Join a specific chat room"""
    try:
        await manager.join_room(room.client_id, room.room)
        return {"status": f"Joined room {room.room}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/leave-room")
async def leave_room(request: Request, room:MessageModelRoom):
    """Leave a specific chat room"""
    try:
        await manager.leave_room(room.client_id, room.room)
        return {"status": f"Left room {room.room}"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, str(e))
    
@router.post('/connect')
async def create_connection(req: ConnectRequest):
    """Generate connection details for WebSocket"""
    try:
        # 1. Authenticate/validate the user (implement your auth logic)
        
        # 2. Generate connection details
        connection_id = str(uuid.uuid4())
        auth_token = str(uuid.uuid4())  # In real app, use JWT
        
        # 3. Store connection metadata (in DB or cache)
        # Example: await cache.set(f"conn:{connection_id}", {
        #     "user_id": request.user_id,
        #     "room_id": request.room_id,
        #     "auth_token": auth_token
        # })
        
        return ConnectionTicket(
            websocket_url=f"ws://yourdomain.com/ws/{req.room_id}?token={auth_token}",
            connection_id=connection_id,
            auth_token=auth_token
        )
        
    except Exception as e:
        raise HTTPException(500, f"Connection failed: {str(e)}")