from __future__ import annotations
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship
    )
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, TYPE_CHECKING
import logging

from src.core.services.database.models.base import Base, int_pk, created_at, updated_at
from src.core.config.config import default_picture_none

if TYPE_CHECKING:
    from src.core.services.auth.domain.models.refresh_token import RefreshTokenModel

logger = logging.getLogger(__name__)


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int_pk]
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    join_date: Mapped[created_at]
    last_time_login: Mapped[updated_at]
    is_active:Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    photo: Mapped[str] = mapped_column(default=default_picture_none, nullable=True)
    otp_secret: Mapped[Optional[str]] = mapped_column(default=None)
    otp_enabled: Mapped[bool] = mapped_column(default=False, nullable=True)
    qrcode_link: Mapped[str] = mapped_column(default=None, nullable=True)

    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"<User(id={self.id}, username={self.login})>"
        
    async def revoke_all_tokens(self, session:AsyncSession):
        """Revoke all refresh tokens for this user"""
        try:
            # Explicitly load the refresh_tokens relationship
            await session.refresh(self, ['refresh_tokens'])
            
            for token in self.refresh_tokens:
                token.revoked = True
                session.add(token)
            
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    def revoke_device_tokens(self, device_info: str):
        """Revoke tokens for a specific device"""
        for token in self.refresh_tokens:
            if token.device_info == device_info:
                token.revoked = True
    @property
    def photo_url(self):
        return f"/media/{self.photo}"