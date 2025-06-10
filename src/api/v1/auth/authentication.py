from fastapi import APIRouter, Form, UploadFile, File
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
import logging

from src.core.schemas.user import UserSchema
from src.core.config.config import settings
from src.core.dependencies.auth_injection import AuthDependency, GET_CURRENT_ACTIVE_USER
from src.core.dependencies.db_injection import DBDI
from src.api.v1.utils.render import render_login_form, render_register_form, render_profile_form
from src.utils.file_uploader import handle_photo_upload
from src.core.services.database.orm.user_orm import update_profile_file


logger = logging.getLogger(__name__)
router = APIRouter(prefix=settings.prefix.api_data.prefix, tags=['auth'])

@router.get("/login")
@router.post("/login")
async def handle_login(
    request: Request,
    auth_service: AuthDependency,
    login: str = Form(None),  # Optional for POST
    password: str = Form(None),  # Optional for POST
    errors: str = None,  # For error passing
):
    if request.method == "POST":
        form_data = {'login': login, 'password': password}
        try:
            tokens = await auth_service.authenticate_user(
                login=login,
                password=password
            )
            
            if not tokens:
                return await render_login_form(
                    request, 
                    errors='Invalid credentials', 
                    form_data=form_data
                )
            
            response = RedirectResponse(url='/', status_code=302)
            response = await auth_service.set_cookies(response=response, tokens=tokens)
            return response
            
        except Exception as err:
            logger.error(f"Login failed: {err}")
            return await render_login_form(
                request, 
                errors='Login failed', 
                form_data=form_data
            )

    # Handle GET request (initial form display)
    return await render_login_form(request)

@router.get("/register")
@router.post("/register")
async def handle_register(
    request: Request,
    auth_service: AuthDependency,
    login: str = Form(None),
    password: str = Form(None),
    password_again: str = Form(None),
    email: str = Form(None),
    errors: str = None
):
    # Handle POST request (form submission)
    if request.method == "POST":
        logger.info(f'User: {login} tries to register...')
        
        try:
            user_data = UserSchema(
            login=login,
            password=password,
            password_again=password_again,
            email=email
            )
            await auth_service.register_user(user_data)
            
            # Successful registration - redirect to login
            return RedirectResponse(url=f"{settings.prefix.api_data.prefix}/login?registered=true", status_code=303)
            
        except IntegrityError as err:
            logger.info(f'{err}')
            return await render_register_form(
                request,
                errors='Username or email already exists',
                form_data={
                    'login': login,
                    'email': email,
                }
            )
        
        except ValidationError as err:
            logger.error(f'{err}')
            return await render_register_form(
                request,
                errors='Registration failed. Passwords not matched',
                form_data={
                    'login': login,
                    'email': email,
                }
            )

        except Exception as err:
            logger.error(f'{err}')
            return await render_register_form(
                request,
                errors='Registration failed. Please try again.',
                form_data={
                    'login': login,
                    'email': email,
                }
            )
    # Handle GET request (initial form display)
    return await render_register_form(request, errors=errors)

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

@router.get('/profile')
async def profile(request: Request, curr_user: GET_CURRENT_ACTIVE_USER):
    if curr_user:
        return await render_profile_form(request, curr_user)

@router.post('/profile')
async def update_profile(
    request: Request,
    curr_user: GET_CURRENT_ACTIVE_USER,
    db:DBDI,
    email: str = Form(...),
    photo: UploadFile = File(None)
):
    if not curr_user:
        return RedirectResponse('/login', status_code=303)
    
    if photo:
        # Handle file upload (you'll need to implement this)
        photo_url = await handle_photo_upload(photo, curr_user)
        
    await update_profile_file(db, curr_user, {'email':email,'photo':photo_url})
    
    return RedirectResponse(f'{settings.prefix.api_data.prefix}/profile', status_code=303)