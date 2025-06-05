from fastapi import HTTPException, status, Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

class AuthException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or "Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def auth_exception_handler(request: Request, exc: AuthException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(AuthException, auth_exception_handler)