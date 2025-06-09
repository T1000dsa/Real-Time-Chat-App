from fastapi import WebSocket
from typing import Optional, Dict
from datetime import datetime, timezone
import httpx
import logging
from pydantic import BaseModel


logger = logging.getLogger(__name__)

class MessageModel(BaseModel):
    sender_id: int
    sender_name: str
    content: str
    timestamp: datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_info: Dict[int, dict] = {}
        self.webhook_url = "https://your-webhook-manager.com/webhook"
        self.messages: list[MessageModel] = []  # Stores chat history

        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, client_id: int, user_info: dict = None):
        logger.info(f"Attempting to connect client {client_id}")
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_info[client_id] = user_info or {}
        logger.info(f"Client {client_id} connected successfully")
        await self.notify_webhook(
            "connection",
            client_id,
            {"status": "connected", "user_info": self.user_info[client_id]}
        )

    async def notify_webhook(self, event_type: str, client_id: int, data: Optional[dict] = None):
        msg = MessageModel(
            sender_id=client_id,
            sender_name=self.user_info,
            content=data,
            timestamp=datetime.now()
        )
        self.messages.append(msg)
        payload = {
            "event": event_type,
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {}
        }
        logger.debug(f"Sending webhook for client {client_id}: {payload}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                logger.info(f"Webhook notification successful for client {client_id}")
            except Exception as e:
                logger.error(f"Webhook error for client {client_id}: {str(e)}")

    def disconnect(self, websocket: WebSocket, client_id: int):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def broadcast(self, message: str, sender_id: int):

        logger.debug(f"Broadcasting message from {sender_id}: {message}")
        payload = {
            "message": message,
            "sender": sender_id,
            "recipients": list(self.active_connections.keys())
        }
        
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to client: {str(e)}")
        
        await self.notify_webhook("message", sender_id, payload)

manager = ConnectionManager()