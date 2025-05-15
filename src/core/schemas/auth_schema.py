from pydantic import BaseModel, field_validator
from datetime import datetime, timezone
from typing import Optional

class Token(BaseModel):
    """Response model for tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshToken(BaseModel):
    user_id: int
    token: str
    expires_at: datetime
    revoked: bool = False
    replaced_by_token: Optional[str] = None  # Changed from bool to Optional[str]
    family_id: str
    previous_token_id: Optional[int] = None
    device_info: Optional[str] = None

    @field_validator('expires_at')
    def ensure_timezone(cls, v):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v