from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.auth.domain.interfaces.TokenRepository import TokenRepository
from src.core.services.database.orm.token_crud import (select_data_token, insert_data_token)


class DatabaseTokenRepository(TokenRepository):
    async def store_refresh_token(self, user_id: int, token: str) -> None:
        # Stores hashed token in DB (e.g., via SQLAlchemy)
        #await db.execute("INSERT INTO refresh_tokens VALUES (...)")
        pass

    async def is_token_revoked(self, session: AsyncSession, token: str) -> bool:
        """Check if token was revoked"""
        hashed_token = self.hash_token(token)
        #$stored_token = await get_refresh_token_data(session, hashed_token)
        #return stored_token is not None and stored_token.revoked
        pass
    
    async def revoke_token(self, token: str) -> None:
        # Marks token as revoked in DB
        #await db.execute("UPDATE refresh_tokens SET revoked=True WHERE token=...")
        pass