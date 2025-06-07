from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated

from src.core.config.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
form_scheme = Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)]