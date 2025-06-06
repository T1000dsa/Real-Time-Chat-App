from fastapi import Response
from datetime import timedelta, datetime
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.auth.domain.interfaces.TokenService import TokenService
from src.core.config.config import settings


class JWTService(TokenService):
    def __init__(self):
        self.secret_key = settings.jwt.key
        self.algorithm = settings.jwt.algorithm

    async def create_token(self, data: dict, expires_delta: timedelta) -> str:
        # Uses PyJWT to create a signed JWT
        return jwt.encode({**data, "exp": datetime.now() + expires_delta}, self.secret_key, self.algorithm)
    
    async def verify_token(self, token: str) -> dict:
        # Validates JWT signature and expiry
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
    
    async def rotate_tokens(
        self, 
        session: AsyncSession,
        refresh_token: str
    ) -> dict:
        pass

    async def set_secure_cookies(self, response:Response, tokens:dict):
        pass

    async def clear_tokens(self, response: Response) -> Response: 
        pass