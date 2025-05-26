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
import bcrypt

from src.core.services.database.models.base import Base, int_pk, created_at, updated_at

if TYPE_CHECKING:
    from src.core.services.database.models.refresh_token import RefreshTokenModel

logger = logging.getLogger(__name__)


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    join_date: Mapped[created_at]
    last_time_login: Mapped[updated_at]
    is_active:Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
    
    def set_password(self, password: str):
        """Securely hash and store password"""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

    def check_password(self, plaintext_password: str) -> bool:
        """Verify password with automatic format correction"""
            
        try:
            return bcrypt.checkpw(plaintext_password.encode('utf-8'), self.password.encode())
        except Exception as err:
            logger.error(f"Password verification failed for user {self.id}: {err}")
            return False
        
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