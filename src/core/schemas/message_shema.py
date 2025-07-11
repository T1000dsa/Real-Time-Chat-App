from pydantic import BaseModel
from typing import Optional


class MessabeSchemaBase(BaseModel):
    user:str
    room_id :str
    room_type:Optional[str] = None

class MessageSchema(MessabeSchemaBase):
    message: str

class DirectMessage(BaseModel):
    actor_id:str
    recipient_id:str
    
class DirectScheme(DirectMessage):
    message: str