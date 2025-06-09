from fastapi import APIRouter
from fastapi.requests import Request
import logging

from src.utils.prepared_response import prepare_template 
from src.core.config.config import templates
from src.core.dependencies.auth_injection import GET_CURRENT_ACTIVE_USER, GET_CURRENT_USER


logger = logging.getLogger(__name__)
router = APIRouter(tags=['api'])

@router.get('/')
async def index(
    request:Request
    ):
    prepared_data = {
        "title":"Main page"
        }
    
    add_data = {
            "request":request
            }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data=add_data
        )

    response = templates.TemplateResponse('index.html', template_response_body_data)
    return response

@router.get('/protected')
async def index(
    request:Request,
    user:GET_CURRENT_USER
    ):
    return "Protected endpoint!!!"


@router.get('/protected11')
async def index(
    request:Request,
    user:GET_CURRENT_ACTIVE_USER
    ):
    return "Protected endpoint!!!"