from abc import ABC, abstractmethod


class HashService(ABC):
    @abstractmethod
    def hash_token(self, token: str) -> str: ...
    
    @abstractmethod
    async def verify_password(self, password: str, hashed_password: str) -> bool: ...

    @abstractmethod
    async def hash_password(self, password:str) -> str: ...


    
    