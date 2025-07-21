from fastapi import APIRouter, Response, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
from typing import Optional
import logging
import pyotp
import io
import qrcode
import base64

from src.core.dependencies.auth_injection import GET_CURRENT_USER, AuthDependency
from src.api.v1.utils.render_auth import render_mfa_form, render_pass_form
from src.api.v1.utils.render_MFA import render_qr_code
from src.core.config.config import main_prefix, EXTERNAL_BASE_URL
from src.api.v1.utils.render_pass_flow import (
    render_after_send_email
    )


logger = logging.getLogger(__name__)
router = APIRouter(prefix=main_prefix)


async def is_otp_correct(otp: Optional[str], secret: str) -> bool:
    return pyotp.TOTP(secret).now() == otp

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
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"QR code generation failed: {e}")
        raise HTTPException(status_code=500, detail="QR code generation failed")

@router.get('/auth/mfa/get_qrcode')
async def get_qrcode(request: Request, user:GET_CURRENT_USER):
    return await render_qr_code(request, user.qrcode_link)
    
@router.post("/auth/mfa/enable")
async def enable_mfa(
    request: Request,
    user: GET_CURRENT_USER,
    auth_service: AuthDependency,
    OPT: str = Form(None),
    errors:str = None
):
    """Verify OTP and enable MFA for user"""
    descr = 'Check your email for qrcode!'


    if not user.qrcode_link: # adjust
        image_base64 = await generate_qr_code(user, auth_service)

        user.qrcode_link = image_base64

        auth_service.session.add(user)
        await auth_service.session.commit()
        await auth_service.session.refresh(user)

        await auth_service._email.send_generated_qrcode(user.email, f'{EXTERNAL_BASE_URL}/v1/auth/mfa/get_qrcode')

        return await render_after_send_email(request, errors, descr)
 
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
    request: Request,
    user: GET_CURRENT_USER,
    auth_service: AuthDependency,
    password: str = Form(None)
):
    """Disable MFA for user (requires password confirmation)"""
    if not password:
        return await render_pass_form(request)
    
    if not await auth_service._hash.verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    # Disable MFA and clear secret
    user.otp_enabled = False
    user.otp_secret = None
    
    auth_service.session.add(user)

    await auth_service.session.commit()
    await auth_service.session.refresh(user)

    
    return {"message": "MFA disabled successfully"}