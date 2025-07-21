from fastapi import Request
import logging 

from src.utils.prepared_response import prepare_template
from src.core.config.config import templates, main_prefix, url_email_verification
from src.core.services.auth.domain.models.user import UserModel
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)

@time_checker
async def render_login_form(
    request: Request,
    errors: str | None = None,
    form_data: dict | None = None
):
    prepared_data = {
        "title":"Sign In",
        "form_data":form_data,
        "errors":errors,
        "url_data":url_email_verification,
        }

    template_response_body_data = await prepare_template(
        data=prepared_data,
        )

    response = templates.TemplateResponse(
        request=request,
        name='users/login.html',
        context=template_response_body_data
        )
    return response

@time_checker
async def render_register_form(
    request: Request,
    errors: str | None = None,
    form_data: dict | None = {}
):
    """Helper function to render the registration template"""
    prepared_data = {
        "title":"Sign Up",
        "form_data":form_data,
        "errors":errors
        }
    
    
    template_response_body_data = await prepare_template(
        data=prepared_data
        )

    response = templates.TemplateResponse(
        request=request,
        name='users/register.html',
        context=template_response_body_data
        )
    return response

@time_checker
async def render_profile_form(request: Request, user: UserModel):
    prepared_data = {
        "title": "Profile"
    }
    
    add_data = {
        "user": user,
        "password_change_url":f'{main_prefix}/password_change',
        "main_prefix":main_prefix
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )

    response = templates.TemplateResponse(
        request=request,
        name='users/profile.html',
        context=template_response_body_data
        )
    return response

@time_checker
async def render_mfa_form(request: Request):
    prepared_data = {
        "title": "Login",
        "content":"Please, provide OTP-code. QR-code was sent on your email, please check!"
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
    )

    response = templates.TemplateResponse(
        request=request,
        name='OTP.html',
        context=template_response_body_data
        )
    return response

@time_checker
async def render_pass_form(request: Request):
    prepared_data = {
        "title": "Login",
        "content":"Please, provide your password"
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
    )

    response = templates.TemplateResponse(
        request=request,
        name='PASS.html',
        context=template_response_body_data
        )
    return response