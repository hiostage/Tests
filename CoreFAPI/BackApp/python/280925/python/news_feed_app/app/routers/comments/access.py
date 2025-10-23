from typing import Annotated

from app_utils.permission import admin_role, auth_user, news_maker_role
from app_utils.validators import validate_user_permission
from dependencies.user import CurrentUserDep
from fastapi import Depends

ReadCommentsUser = CurrentUserDep
CommentsUser = Annotated[
    CurrentUserDep,
    Depends(validate_user_permission(admin_role, auth_user, news_maker_role)),
]
