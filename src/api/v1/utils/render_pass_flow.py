from fastapi import Request
import logging 

from src.utils.prepared_response import prepare_template
from src.core.config.config import templates, main_prefix, main_url
from src.core.services.auth.domain.models.user import UserModel
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)


@time_checker
async def render_pass_change(
    request: Request, 
    user: UserModel,
    errors:str = None
    ):
    prepared_data = {
        "title": "Password Change",
        "description":"Are you sure you want to change password? If so, you have to provide your email.",
        "errors":errors
    }
    
    add_data = {
        "user": user,
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )

    response = templates.TemplateResponse(
        request=request,
        name='users/password_change.html',
        context=template_response_body_data
        )
    return response

@time_checker
async def render_verification_success(
    request: Request, 
    user: UserModel,
    errors:str = None
):
    prepared_data = {
        "title": "Email Verification Success!",
        "description":"You managed to verificate email. You can proceed change password",
        "url_data":{'title':'password reset', 'url':f"{main_url}{main_prefix}/reset_password"},
        "errors":errors
    }
    
    add_data = {
        "user": user,
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )

    response = templates.TemplateResponse(
        request=request,
        name='generic_answer.html',
        context=template_response_body_data
        )
    return response


@time_checker
async def render_password_reset(
    request: Request, 
    user: UserModel,
    errors:str = None
):
    prepared_data = {
        "title": "Password Reset",
        "description":"Carefully choice password. It should be more than 0 and less than 128 characters.",
        "errors":errors
        
    }
    
    add_data = {
        "user": user,
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )

    response = templates.TemplateResponse(
        request=request,
        name='users/password_reset.html',
        context=template_response_body_data
        )
    return response


@time_checker
async def render_after_send_email(
    request: Request, 
    user: UserModel,
    errors:str = None
):
    prepared_data = {
        "title": "Check your email!",
        "description":"You have been successfully provided email, now check your email for reset password link",
        "errors":errors
    }
    
    add_data = {
        "user": user,
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )

    response = templates.TemplateResponse(
        request=request,
        name='generic_answer.html',
        context=template_response_body_data
        )
    return response