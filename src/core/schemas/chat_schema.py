from pydantic import BaseModel
from typing import Optional

class BaseMessage(BaseModel):
    action: str

class JoinRoomMessage(BaseMessage):
    room_id: str

class ChatMessage(BaseMessage):
    content: str
    room_id: str