from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.auth.domain.models.user import UserModel
from src.core.services.auth.infrastructure.services.User_Crud import UserService


class EmailRepo(ABC):
    @abstractmethod
    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool: ...
    
    @abstractmethod
    async def send_verification_email(self, recipient: str, token: str) -> bool: ...

    #@abstractmethod
    #async def send_password_reset_email(self, recipient: str, token: str) -> bool: ...

    @abstractmethod
    async def email_verification(self, session: AsyncSession, email: str,  user_repo: UserService, user: UserModel): ...