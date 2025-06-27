from src.core.services.chat.infrastructure.services.MessageService import MessageService
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.domain.interfaces.ChatManagerRepo import ChatManagerRepo
#from src.core.services.chat.infrastructure.services.ConnectionManager import ConnectionManager


class ChatManager(ChatManagerRepo):
    def __init__(self, message_repo:MessageService, room_service:RoomService):
        self._msg_repo = message_repo
        self._room_serv = room_service