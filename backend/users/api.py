from django.contrib.auth import authenticate
from ninja import Router
from ninja.errors import HttpError

from core.api import create_token
from .models import User
from .schemas import LoginSchema, TokenSchema, UserOut

router = Router()


@router.post('/login', response=TokenSchema, auth=None)
def login(request, payload: LoginSchema):
    user = authenticate(
        request,
        username=payload.username,
        password=payload.password
    )
    if not user:
        raise HttpError(401, '用户名或密码错误')
    if not user.is_active:
        raise HttpError(403, '用户已被禁用')
    token = create_token(user)
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'full_name': user.full_name,
    }


@router.get('/me', response=UserOut)
def get_me(request):
    return request.user
