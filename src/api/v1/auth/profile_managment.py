from fastapi import APIRouter, Form, UploadFile, File, Depends
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
import logging

from src.core.config.config import main_prefix
from src.core.dependencies.auth_injection import (
    AuthDependency,
    GET_CURRENT_ACTIVE_USER,
    get_current_active_user, 
    GET_CURRENT_USER_FOR_EMAIL
    )
from src.api.v1.utils.render_pass_flow import (
    render_pass_change, 
    render_verification_success, 
    render_password_reset, 
    render_after_send_email
    )
from src.api.v1.utils.render_auth import render_profile_form
from src.utils.file_uploader import handle_photo_upload
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)
router = APIRouter(prefix=main_prefix, tags=['auth'])

@time_checker
@router.get('/profile')
async def profile(request: Request, curr_user: GET_CURRENT_ACTIVE_USER):
    logger.debug('Inside profile endpoint')
    if curr_user:
        logger.debug(f'{curr_user=}')
        return await render_profile_form(request, curr_user)

@time_checker
@router.post('/profile')
async def update_profile(
    request: Request,
    curr_user: GET_CURRENT_ACTIVE_USER,
    auth:AuthDependency,
    email: str = Form(None),
    login: str = Form(None),
    photo: UploadFile = File(None)
):
    logger.debug('Inside profile update endpoint')
    if not curr_user:
        return RedirectResponse(f'/{main_prefix}/login', status_code=303)
    
    if photo:
        # Handle file upload (you'll need to implement this)
        photo_url = await handle_photo_upload(photo, curr_user)
        
    await auth.update_profile_user(curr_user.id, {'email':email,'photo':photo_url, 'login':login})
    return RedirectResponse(f'{main_prefix}/profile', status_code=303)

@time_checker
@router.get('/password_change')
@router.post('/password_change')
async def password_change(
    request: Request,
    auth:AuthDependency,
    curr_user:GET_CURRENT_USER_FOR_EMAIL,
    email: str = Form(None),
    errors: str = None
):
    user = None
    
    if curr_user is None:
        user = await auth._repo.get_user_for_auth_by_email(auth.session, email)

    logger.debug(f'{user=} {curr_user=} {email=}')

    if request.method == 'POST':

        try:
            # if user authorised
            if curr_user:
                # Trying to verificate user email, if matches -> go further if not, raise error
                await auth._email.email_verification(auth.session, email, auth._repo, curr_user)

                # Trying to send verificate-link toward urer email
                await auth._email.send_verification_email(email)

                return await render_after_send_email(request, errors)
            # in else case
            else:
                await auth._email.email_verification(auth.session, email, auth._repo)

                await auth._email.send_verification_email(email)

                return await render_after_send_email(request, errors)

        except KeyError as err:
            logger.error(err)
            return await render_pass_change(
                request,
                user=user,
                errors=str(err),
            )

        except Exception as err:
            logger.error(err)
            return await render_pass_change(
                request,
                user=user,
                errors=str(err),
            )
            
    return await render_pass_change(request, user, errors)

@router.get('/verify_email')
async def verificate_email(
    request: Request,
):
    logger.debug(f"user  verificated email successfully")
    return await render_verification_success(request)

@time_checker
@router.get('/reset_password')
@router.post('/reset_password')
async def reset_password(
    request: Request,
    auth:AuthDependency,
    curr_user:GET_CURRENT_USER_FOR_EMAIL,
    email: str = Form(None),
    new_password = Form(None),
    errors: str = None
):
    user = None
    if curr_user is None:
        user = await auth._repo.get_user_for_auth_by_email(auth.session, email)

    logger.debug(f'{curr_user=} {user=} {email=}')

    respone = RedirectResponse(url='/', status_code=302)
    if request.method == 'POST':
        try:
            if curr_user:
                logger.debug(new_password)
                await auth.password_change(curr_user, new_password, email)
                logger.debug('Password was changed successfully')
                return respone
            
            if user:
                logger.debug(new_password)
                await auth.password_change(user, new_password, email)
                logger.debug('Password was changed successfully')
                return respone
            
        except KeyError as err:
            logger.error(err)
            return await render_password_reset(
                request,
                user=user,
                errors=str(err),
            )
        except Exception as err:
            logger.error(err)
            return await render_password_reset(
                request,
                user=user,
                errors=str(err),
            )

    return await render_password_reset(request, user, errors)