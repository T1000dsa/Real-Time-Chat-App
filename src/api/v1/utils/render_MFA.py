from fastapi import Request
import logging 

from src.utils.prepared_response import prepare_template
from src.core.config.config import templates, main_prefix, url_email_verification
from src.core.services.auth.domain.models.user import UserModel
from src.utils.time_check import time_checker

logger = logging.getLogger(__name__)

@time_checker
async def render_qr_code(request: Request, image:str):
    prepared_data = {
        "title": "QR-code",
    }
    
    add_data = {
        "image":image
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