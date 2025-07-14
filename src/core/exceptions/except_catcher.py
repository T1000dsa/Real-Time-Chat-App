from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from functools import wraps
import logging
import asyncio

logger = logging.getLogger(__name__)


from src.core.config.config import templates
from src.utils.prepared_response import prepare_template


def exception_handler(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise e
                
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise e
                
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


async def not_found_exception_handler(request: Request, exc: HTTPException):
    prepared_data = {
        "title": 'There is no such page!',
        "content": "There is no such page! Please return to the main page."
    }
    
    template_response_body_data = await prepare_template(data=prepared_data)

    return templates.TemplateResponse(
        request=request,
        name='404.html',
        context=template_response_body_data,
        status_code=404
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return await not_found_exception_handler(request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )