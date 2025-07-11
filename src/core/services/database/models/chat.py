from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String
from typing import Optional
from datetime import datetime

from .base import Base, int_pk, created_at
from src.core.services.auth.domain.models.user import UserModel


class MessageModel(Base):
    __tablename__ = 'messages'
    
    id: Mapped[int_pk]
    room_id: Mapped[str] = mapped_column(String)
    room_type: Mapped[str] = mapped_column(String, default=None, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer) #ForeignKey("users.id", ondelete='CASCADE'))
    message: Mapped[str]
    created_at: Mapped[created_at]
    is_read: Mapped[bool] = mapped_column(default=False)

    #user: Mapped["UserModel"] = relationship()
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

class DirectModel(Base):
    __tablename__ = 'directs'

    id: Mapped[int_pk]
    actor_id: Mapped[str]
    recipient_id: Mapped[str]
    message: Mapped[str]
    created_at: Mapped[created_at]