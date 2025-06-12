from fastapi import APIRouter, Form
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
import logging

from src.core.schemas.user import UserSchema
from src.core.config.config import main_prefix
from src.core.dependencies.auth_injection import AuthDependency, GET_CURRENT_ACTIVE_USER
from src.api.v1.utils.render import render_login_form, render_register_form, render_profile_form
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)
router = APIRouter(prefix=main_prefix, tags=['auth'])

@time_checker
@router.get("/login")
async def show_login_form(request: Request, errors: str = None):
    """Handle GET requests for login page"""
    return await render_login_form(request, errors=errors)

@time_checker
@router.post("/login")
async def handle_login(
    request: Request,
    auth_service: AuthDependency,
    login: str = Form(...),
    password: str = Form(...),
):
    """Handle POST requests for login form submission"""

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
            errors="Something went wrong", # 'Something went wrong'
            form_data=form_data
        )

@time_checker
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
            return RedirectResponse(url=f"{main_prefix}/login?registered=true", status_code=303)
            
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

@time_checker
@router.get('/logout')
async def logout(
    request: Request,
    auth_service: AuthDependency
):

    logger.debug('Trying to logout...')
    
    try:
        response = await auth_service.logout(request=request)

    except Exception as e:
        logger.debug(f"Unexpected error: {e}")
    return response