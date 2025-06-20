from fastapi import HTTPException, status, Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

class AuthException(HTTPException):
    def __init__(
            self, 
            status_code: str = None,
            detail: str = None,
            headers: dict = {}
            ):
        super().__init__(
            status_code=status_code or status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )

async def auth_exception_handler(request: Request, exc: AuthException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

auth_demand_exception = AuthException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Need to authorize",
            headers={"WWW-Authenticate": "Bearer"},
        )

credentials_exception = AuthException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login or Password is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )


inactive_user_exception = AuthException(
    detail="inactive_user",
)

false_activation_user_exception = AuthException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="This user already active/inactive",
)

#def setup_exception_handlers(app: FastAPI):
    #app.add_exception_handler(AuthException, auth_exception_handler)