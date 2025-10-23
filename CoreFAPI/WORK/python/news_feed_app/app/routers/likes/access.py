from typing import Annotated

from app_utils.permission import admin_role, auth_user, news_maker_role
from app_utils.validators import validate_user_permission
from dependencies.user import CurrentUserDep
from fastapi import Depends

ReadLikesUser = CurrentUserDep
LikesUser = Annotated[
    CurrentUserDep,
    Depends(validate_user_permission(admin_role, news_maker_role, auth_user)),
]
