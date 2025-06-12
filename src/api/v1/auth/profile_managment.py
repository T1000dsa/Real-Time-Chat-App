from fastapi import APIRouter, Form, UploadFile, File
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
import logging

from src.core.config.config import main_prefix
from src.core.dependencies.auth_injection import AuthDependency, GET_CURRENT_ACTIVE_USER
from src.api.v1.utils.render import render_profile_form, render_pass_change
from src.utils.file_uploader import handle_photo_upload
from src.utils.time_check import time_checker


logger = logging.getLogger(__name__)
router = APIRouter(prefix=main_prefix, tags=['auth'])

@time_checker
@router.get('/profile')
async def profile(request: Request, curr_user: GET_CURRENT_ACTIVE_USER):
    if curr_user:
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
    if not curr_user:
        return RedirectResponse(f'/{main_prefix}/login', status_code=303)
    
    if photo:
        # Handle file upload (you'll need to implement this)
        photo_url = await handle_photo_upload(photo, curr_user)
        
         #update_profile_file(db, curr_user, {'email':email,'photo':photo_url, 'login':login})
    await auth.update_profile_user(curr_user.id, {'email':email,'photo':photo_url, 'login':login})
    return RedirectResponse(f'{main_prefix}/profile', status_code=303)



@time_checker
@router.get('/password_change')
@router.post('/password_change')
async def password_change(
    request: Request,
    curr_user: GET_CURRENT_ACTIVE_USER,
    email: str = Form(None),
):
    if request.method == 'POST':
        pass

    return await render_pass_change(request, curr_user)