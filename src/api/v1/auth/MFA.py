from fastapi import APIRouter, Response, HTTPException
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
def generate_qr_code(user: GET_CURRENT_USER):
    # Generate a more appropriate OTP secret
    secret = pyotp.random_base32()
    
    # Store this secret with the user account (pseudo-code)
    # user.otp_secret = secret
    # await user.save()
    
    totp = pyotp.TOTP(secret)
    try:
        qr_code = qrcode.make(
            totp.provisioning_uri(name=user.login, issuer_name="YourAppName"),
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        img_byte_arr = io.BytesIO()
        qr_code.save(img_byte_arr, format="PNG")
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
    except Exception as e:
        logger.error(f"QR code generation failed: {e}")
        raise HTTPException(status_code=500, detail="QR code generation failed")