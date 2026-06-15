from datetime import datetime
from ninja import Schema


class LoginSchema(Schema):
    username: str
    password: str


class TokenSchema(Schema):
    token: str
    user_id: int
    username: str
    role: str
    full_name: str


class UserOut(Schema):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    date_joined: datetime
