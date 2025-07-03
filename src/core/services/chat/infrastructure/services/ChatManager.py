from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.chat.infrastructure.services.MessageService import MessageService
from src.core.services.chat.infrastructure.services.RoomService import RoomService
from src.core.services.chat.domain.interfaces.ChatManagerRepo import ChatManagerRepo
from src.core.services.chat.infrastructure.services.DBService import DBService


class ChatManager(ChatManagerRepo):
    def __init__(self, session:AsyncSession, message_repo:MessageService, room_service:RoomService, db_service:DBService):
        self.session = session
        self._msg_repo = message_repo
        self._room_serv = room_service
        self._db_service = db_service