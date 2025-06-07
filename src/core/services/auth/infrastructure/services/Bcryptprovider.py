from passlib.context import CryptContext
import logging

from src.core.services.auth.domain.interfaces.HashService import HashService


logger = logging.getLogger(__name__)

class Bcryptprovider(HashService):
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def hash_token(self, token: str) -> str:
        return self.pwd_context.hash(token)
    
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        if not isinstance(password, (str, bytes)):
            raise ValueError("Password must be string or bytes")
        if not isinstance(hashed_password, str):
            raise ValueError("Hashed password must be string")
        try:
            return self.pwd_context.verify(password, hashed_password)
        except Exception as err:
            logger.error(f"{err} {password=} {hashed_password=}")
            raise err
        
    async def hash_password(self, password):
        self.pwd_context.hash(password)