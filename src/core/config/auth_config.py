from fastapi import HTTPException, status, Depends
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from authlib.integrations.starlette_client import OAuth
from typing import Any, Dict, Annotated

from src.core.config.config import settings


oauth = OAuth()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
form_scheme = Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)]

SECRET_KEY = settings.jwt.key
ALGORITHM = settings.jwt.algorithm

ACCESS_TYPE = 'access'
REFRESH_TYPE = 'refresh'
CSRF_TYPE = 'csrf'

class AuthException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: Any = None,
        headers: Dict[str, str] | None = None,
        error: str | None = None,
        error_description: str | None = None
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        if error:
            if not detail:
                detail = {}
            if isinstance(detail, dict):
                detail.update({"error": error})
                if error_description:
                    detail.update({"error_description": error_description})
        super().__init__(status_code=status_code, detail=detail, headers=headers)

credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

inactive_user_exception = AuthException(
    error="inactive_user",
    error_description="The user is inactive"
)