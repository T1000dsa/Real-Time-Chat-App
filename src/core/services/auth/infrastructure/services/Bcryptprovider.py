from passlib.context import CryptContext

from src.core.services.auth.domain.interfaces.HashService import HashService
from src.core.services.auth.domain.models.user import UserModel


class Bcryptprovider(HashService):
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def hash_token(self, token: str) -> str:
        return self.pwd_context.hash(token)
    
    async def verify_password(self, user: UserModel, password: str) -> bool:
        return self.pwd_context.verify(password, user.password)
    
    async def hash_password(self, password):
        self.pwd_context.hash(password)