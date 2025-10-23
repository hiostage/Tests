import uuid

from app_utils.permission import admin_role, anonymous_role, auth_user, news_maker_role
from schemas.users import User

fake_admin_user = User(id=uuid.uuid4(), roles=[admin_role])
fake_news_maker_user = User(id=uuid.uuid4(), roles=[news_maker_role])
fake_news_maker_user_2 = User(id=uuid.uuid4(), roles=[news_maker_role])
fake_auth_user = User(id=uuid.uuid4(), roles=[auth_user])
fake_anonymous_user = User(id=None, roles=[anonymous_role])
