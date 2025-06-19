from pydantic import BaseModel


class MessabeSchemaBase(BaseModel):
    user_id:int
    room_id :str

class MessageSchema(MessabeSchemaBase):
    message: str

class ConnectionTicket(BaseModel):
    websocket_url: str
    connection_id: str
    auth_token: str

class ConnectRequest(BaseModel):
    user_id: str  # Or any other auth data
    room_id: str