from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import logging
import pyotp
import io
import qrcode

from src.core.dependencies.auth_injection import GET_CURRENT_USER


logger = logging.getLogger(__name__)
router = APIRouter()


async def is_otp_correct(otp: Optional[str], secret: str) -> bool:
    return pyotp.TOTP(secret).now() == otp

@router.get("/auth/otp/generate")
def generate_qr_code(user:GET_CURRENT_USER):
    secret = uuid4()
    totp = pyotp.TOTP(secret)
    qr_code = qrcode.make(
        totp.provisioning_uri(name=user.login, issuer_name="Test")
    )
    img_byte_arr = io.BytesIO()
    qr_code.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()
    return Response(content=img_byte_arr, media_type="image/png")