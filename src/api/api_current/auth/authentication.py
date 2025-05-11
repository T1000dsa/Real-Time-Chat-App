from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


router = APIRouter()

@router.get('/login')
async def html_form_login():
    pass

@router.get('/register')
async def html_form_register():
    pass

@router.post('/login/check')
async def login():
    pass

@router.post('/register/check')
async def register():
    pass