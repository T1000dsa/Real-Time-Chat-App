from fastapi import APIRouter, Response, HTTPException, Form, Request
from typing import Optional
import logging
import pyotp
import io
import qrcode

from src.core.dependencies.auth_injection import GET_CURRENT_USER, AuthDependency
from src.api.v1.utils.render_auth import render_mfa_form
from src.core.config.config import main_prefix


logger = logging.getLogger(__name__)
router = APIRouter(prefix=main_prefix)


async def is_otp_correct(otp: Optional[str], secret: str) -> bool:
    return pyotp.TOTP(secret).now() == otp

@router.get("/auth/otp/generate")
async def generate_qr_code(
    user: GET_CURRENT_USER,
    auth_service: AuthDependency
):
    secret = pyotp.random_base32()
    
    # Store the secret (but don't enable MFA yet)
    user.otp_secret = secret
    auth_service.session.add(user)

    await auth_service.session.commit()
    await auth_service.session.refresh(user)
    

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
    
    
@router.post("/auth/mfa/enable")
async def enable_mfa(
    request: Request,
    user: GET_CURRENT_USER,
    auth_service: AuthDependency,
    OPT: str = Form(None)
):
    """Verify OTP and enable MFA for user"""
    if not OPT:
        return await render_mfa_form(request)
    
    logger.debug(f"{user.otp_secret=} {OPT=}")
    logger.debug(pyotp.TOTP(user.otp_secret).verify(OPT, valid_window=10))
    
    if not user.otp_secret:
        raise HTTPException(status_code=400, detail="Generate OTP secret first")
    

    
    if not pyotp.TOTP(user.otp_secret).verify(OPT, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    # Enable MFA for the user
    user.otp_enabled = True
    auth_service.session.add(user)

    await auth_service.session.commit()
    await auth_service.session.refresh(user)
    
    return {"message": "MFA enabled successfully"}


@router.post("/auth/mfa/disable")
async def disable_mfa(
    user: GET_CURRENT_USER,
    auth_service: AuthDependency,
    password: str = Form(...)
):
    """Disable MFA for user (requires password confirmation)"""
    if not await auth_service.verify_password(user.login, password):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    # Disable MFA and clear secret
    user.otp_enabled = False
    user.otp_secret = None
    
    auth_service.session.add(user)

    await auth_service.session.commit()
    await auth_service.session.refresh(user)
    
    return {"message": "MFA disabled successfully"}