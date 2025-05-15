from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from jose import JWTError
import logging

from src.core.services.auth.token_service import TokenService
from src.core.services.auth.user_service import UserService
from src.core.schemas.User import UserSchema
from src.core.config.config import templates, settings
from src.utils.prepared_response import prepare_template
from src.core.dependencies.db_injection import DBDI
from src.core.dependencies.auth_injection import get_token_service, get_auth_service, GET_CURRENT_ACTIVE_USER
from src.core.config.auth_config import (
    ACCESS_TYPE, 
    REFRESH_TYPE,
    CSRF_TYPE, 
    form_scheme
    )

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
            "request":request
        })

    response = templates.TemplateResponse('users/login.html', template_response_body_data)
    return response


@router.post("/login/process")
async def login(
    request: Request,
    form_data: form_scheme,
    auth_service: UserService = Depends(get_auth_service)
):

    try:
        tokens = await auth_service.authenticate_user(
            username=form_data.username,
            password=form_data.password
        )
        
        if not tokens:
            return await html_login(request=request, error='Invalid credentials')
        
        response = RedirectResponse(url='/', status_code=302)
        await auth_service.token_service.set_secure_cookies(
            response=response,
            access_token=tokens[ACCESS_TYPE],
            refresh_token=tokens[REFRESH_TYPE],
            csrf_token=tokens.get(CSRF_TYPE)
        )
        
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
            "request":request
        })
    
    response = templates.TemplateResponse('users/register.html', template_response_body_data)
    return response

@router.post("/register/process")
async def register(
    request:Request,
    session: DBDI,
    auth_service: UserService = Depends(get_auth_service),
    username: str = Form(...),
    password: str = Form(...),
    password_again: str = Form(...),
    mail: str = Form(""),
    bio: str = Form("")
):

    logger.info('inside register')

    user_data = UserSchema(
        username=username,
        password=password,
        password_again=password_again,
        mail=mail,
        bio=bio
    )

    user = auth_service
    try:
        await user.create_user(user_data)
 
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
            "request":request
        })
    return templates.TemplateResponse('users/register_success.html', template_response_body_data)


@router.get('/logout')
async def logout(
    request: Request,
    auth_service: UserService = Depends(get_auth_service)
):
    response = RedirectResponse(url=router.prefix + "/login")
    
    # Try to get token from cookies
    token = request.cookies.get(ACCESS_TYPE)
    
    if token:
        try:
            await auth_service.logout_user(token, ACCESS_TYPE)
        except (JWTError, ValueError) as e:
            logger.debug(f"Token error during logout: {e}")
    
    # Delete cookies
    for cookie_name in [ACCESS_TYPE, REFRESH_TYPE, CSRF_TYPE]:
        response.delete_cookie(
            cookie_name,
            path="/",
            domain=None,
            secure=True,
            httponly=True
        )
    return response


@router.post("/refresh")
async def refresh_tokens(
    request: Request,
    session: DBDI,
    token_service: TokenService = Depends(get_token_service)
):
    refresh_token = request.cookies.get(REFRESH_TYPE)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    try:
        new_tokens = await token_service.rotate_tokens(session, refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token rotation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    response = RedirectResponse(url='/', status_code=302)
    await token_service.set_secure_cookies(
        response=response,
        access_token=new_tokens[ACCESS_TYPE],
        refresh_token=new_tokens[REFRESH_TYPE],
        csrf_token=new_tokens.get(CSRF_TYPE)
    )
    return response