from pydantic import BaseModel


class MessageModel(BaseModel):
    message: str

class MessageModelRoom(BaseModel):
    client_id:str
    room :str

class ConnectionTicket(BaseModel):
    websocket_url: str
    connection_id: str
    auth_token: str

class ConnectRequest(BaseModel):
    user_id: str  # Or any other auth data
    room_id: str