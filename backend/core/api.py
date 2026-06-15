import datetime
import jwt
from django.conf import settings
from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.security import HttpBearer

from users.models import User


class AuthBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            request.user = user
            return user
        except Exception:
            return None


def create_token(user: User) -> str:
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


api = NinjaAPI(
    title='商场儿童推车管理系统 API',
    description='儿童推车滞留回收与跨楼层调拨系统接口文档',
    auth=AuthBearer(),
    version='1.0.0'
)

from users.api import router as users_router
from stations.api import router as stations_router
from carts.api import router as carts_router
from rentals.api import router as rentals_router
from transfers.api import router as transfers_router
from stranded.api import router as stranded_router
from dashboard.api import router as dashboard_router

api.add_router('/auth', users_router, tags=['认证与用户'])
api.add_router('/stations', stations_router, tags=['服务点管理'])
api.add_router('/carts', carts_router, tags=['推车档案'])
api.add_router('/rentals', rentals_router, tags=['借还登记'])
api.add_router('/transfers', transfers_router, tags=['跨点调拨'])
api.add_router('/stranded', stranded_router, tags=['滞留上报'])
api.add_router('/dashboard', dashboard_router, tags=['调度看板'])
