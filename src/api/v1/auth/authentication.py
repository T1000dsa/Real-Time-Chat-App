from fastapi import APIRouter, Form
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
import logging

from src.core.schemas.User import UserSchema, UserBase
from src.core.config.config import templates, settings
from src.utils.prepared_response import prepare_template
from src.frontend.menu.urls import choice_from_menu, menu_items
from src.core.dependencies.auth_injection import AuthDependency
from src.core.config.auth_config import form_scheme


logger = logging.getLogger(__name__)
router = APIRouter(prefix=settings.prefix.api_data.prefix, tags=['auth'])


@router.get("/login")
async def html_login(
    request:Request,
    error:str|None = None
    ):

    prepared_data = {
        "title":"Sigh In",
        "template_action":settings.prefix.api_data.prefix+'/login/process',
        "error":error
        }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data={
            "request":request,
            "menu_data":choice_from_menu,
            "menu":menu_items
        })

    response = templates.TemplateResponse('users/login.html', template_response_body_data)
    return response


@router.post("/login/process")
async def login(
    request: Request,
    auth_service: AuthDependency,
    login: str = Form(...),
    password: str = Form(...),
):
    logger.debug(auth_service)

    try:
        tokens = await auth_service.authenticate_user(
            login=login,
            password=password
        )
        
        if not tokens:
            return await html_login(request=request, error='Invalid credentials')
        logger.debug('after tokens check')
        
        response = await auth_service.set_cookies(response=RedirectResponse(url='/', status_code=302), tokens=tokens)
        return response
        
    except Exception as err:
        logger.error(f"Login failed: {err}")
        return await html_login(request=request, error='Login failed')

@router.get("/register")
async def html_register(
    request:Request
):
    logger.info('inside html_register')

    prepared_data = {
        "title":"Sigh Up",
        "template_action":settings.prefix.api_data.prefix+'/register/process',
        }
    
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data={
            "request":request,
            "menu_data":choice_from_menu,
            "menu":menu_items
        })
    
    response = templates.TemplateResponse('users/register.html', template_response_body_data)
    return response

@router.post("/register/process")
async def register(
    request:Request,
    auth_service: AuthDependency,
    login: str = Form(...),
    password: str = Form(...),
    password_again: str = Form(...),
    mail: str = Form(""),
    bio: str = Form("")
    
):

    logger.info(f'User: {login} tries to regist...')

    user_data = UserSchema(
        login=login,
        password=password,
        password_again=password_again,
        mail=mail,
        bio=bio
    )

    try:
        await auth_service.register_user(user_data)
 
    except IntegrityError as err:
        logger.info(f'{err}') 
        return "Such user already in database"

    except Exception as err:
        logger.error(f'{err}')
        raise err
    
    prepared_data = {
        "title":"Registration success",
        "content":"Registration was success!"
        }
    
    logger.info('success registration')
    template_response_body_data = await prepare_template(
        data=prepared_data,
        additional_data={
            "request":request,
            "menu_data":choice_from_menu,
            "menu":menu_items
        })
    return templates.TemplateResponse('users/register_success.html', template_response_body_data)


@router.get('/logout')
async def logout(
    request: Request,
    auth_service: AuthDependency
):
    response = RedirectResponse(url='/')
    logger.debug('Tring to logout...')
    
    try:
        response = await auth_service.logout(request=request, response=response)

    except Exception as e:
        logger.debug(f"Unexpected error: {e}")
    
    return response