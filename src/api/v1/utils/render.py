from fastapi import Request
import logging 

from src.utils.prepared_response import prepare_template
from src.core.config.config import templates
from src.core.services.auth.domain.models.user import UserModel


logger = logging.getLogger(__name__)

async def render_login_form(
    request: Request,
    errors: str | None = None,
    form_data: dict | None = None
):
    prepared_data = {
        "title":"Sigh In",
        "form_data":form_data,
        "errors":errors
        }
    
    add_data = {
            "request":request
        }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
        )

    response = templates.TemplateResponse('users/login.html', template_response_body_data)
    return response

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
    
    add_data = {
            "request":request
        }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
        )

    response = templates.TemplateResponse('users/register.html', template_response_body_data)
    return response

async def render_profile_form(request: Request, user: UserModel):
    prepared_data = {
        "title": "Profile"
    }
    
    add_data = {
        "request": request,
        "user": user,
    }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
    )

    return templates.TemplateResponse('users/profile.html', template_response_body_data)