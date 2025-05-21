from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from .base import Base, int_pk, created_at
from .user import UserModel

class ChatRoom(Base):
    __tablename__ = 'chat_rooms'
    
    id: Mapped[int_pk]
    name: Mapped[str]
    created_at: Mapped[created_at]
    is_active: Mapped[bool] = mapped_column(default=True)
    
    messages: Mapped[list["Message"]] = relationship(back_populates="room")
    participants: Mapped[list["ChatParticipant"]] = relationship(back_populates="room")

class Message(Base):
    __tablename__ = 'messages'
    
    id: Mapped[int_pk]
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id", ondelete='CASCADE'))  # Added ForeignKey
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    content: Mapped[str]
    created_at: Mapped[created_at]
    is_read: Mapped[bool] = mapped_column(default=False)
    
    room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    user: Mapped["UserModel"] = relationship()

class ChatParticipant(Base):
    __tablename__ = 'chat_participants'
    
    id: Mapped[int_pk]
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id", ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    joined_at: Mapped[created_at]
    
    room: Mapped["ChatRoom"] = relationship(back_populates="participants")
    user: Mapped["UserModel"] = relationship()