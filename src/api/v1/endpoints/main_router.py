from fastapi import APIRouter
from fastapi.requests import Request
import logging

from src.utils.prepared_response import prepare_template 
from src.core.config.config import templates


logger = logging.getLogger(__name__)
router = APIRouter(tags=['api'])

@router.get('/')
async def index(
    request:Request
    ):
    prepared_data = {
        "title":"Main page"
        }
    
    
    template_response_body_data = await prepare_template(
        data=prepared_data
        )

    response = templates.TemplateResponse(
        request=request,
        name='index.html',
        context=template_response_body_data
    )
    return response