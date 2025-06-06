from src.core.services.auth.domain.interfaces import UserAuthProvider, TokenService, TokenRepository, HashService

class LoginUseCase:
    def __init__(
        self,
        auth_provider: UserAuthProvider,
        token_service: TokenService,
        token_repository: TokenRepository,  # Renamed for consistency
        hash_service: HashService
    ):
        if not all([auth_provider, token_service, token_repository, hash_service]):
            raise ValueError("Dependencies cannot be None")
        self._auth = auth_provider
        self._tokens = token_service
        self._repo = token_repository  # Shorter, but clear
        self._hash_serv = hash_service  