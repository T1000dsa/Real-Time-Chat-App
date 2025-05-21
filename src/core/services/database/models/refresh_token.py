from __future__ import annotations
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship
    )
from sqlalchemy import String, ForeignKey, TypeDecorator, DateTime, Boolean
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from src.core.services.database.models.base import Base

if TYPE_CHECKING:
    from src.core.services.database.models.user import UserModel  # Path to your UserModel


class NaiveDateTime(TypeDecorator):
    """Ensures all datetimes are stored as naive UTC"""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.replace(tzinfo=None)
    

class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(NaiveDateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False)
    replaced_by_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        NaiveDateTime,
        default=lambda: datetime.utcnow(),  # Use lambda to get current time on each insert
        nullable=False
    )
    family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(200))
    previous_token_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("refresh_tokens.id"), 
        nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["UserModel"] = relationship(back_populates="refresh_tokens")