from sqlalchemy.orm import (
    mapped_column,
    Mapped
    )
from typing import Optional
import logging
import bcrypt

from src.core.services.database.postgres.models.base import Base, int_pk, created_at, updated_at


logger = logging.getLogger(__name__)


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int_pk]
    username: Mapped[str]
    password: Mapped[str]
    mail: Mapped[Optional[str]]
    bio: Mapped[Optional[str]]
    join_data: Mapped[created_at]
    last_time_login: Mapped[updated_at]
    is_active:Mapped[bool] = mapped_column(default=True, nullable=True)
    is_super_user: Mapped[bool] = mapped_column(default=False)

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
