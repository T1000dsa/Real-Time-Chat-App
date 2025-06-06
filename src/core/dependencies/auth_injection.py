from src.core.services.auth.domain.interfaces import TokenService, TokenRepository, HashService

from src.core.services.auth.infrastructure import JWTService, DatabaseTokenRepository

def get_token_service() -> TokenService:
    return JWTService()

def get_token_repo() -> TokenRepository:
    return DatabaseTokenRepository()

def get_hash_service() -> HashService:
    return 