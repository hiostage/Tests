from typing import Annotated
from uuid import UUID

from app_utils.permission import admin_role, anonymous_role
from core.classes.app import CustomFastApi
from core.classes.settings import Settings
from fastapi import Depends, Request
from schemas.users import User


async def get_user(request: Request) -> User:
    """
    Возвращаем текущего пользователя.

    :param request: Request.
    :return: User.
    """
    # TODO: Дописать, когда станет понятнее с пользователями. Пока возвращаем фэйкового пользователя.
    #   Важно: Пользователя возвращаем всегда, даже если это аноним, пример: User(id=None, roles=[anonymous_role])
    #   Важно: Роли всегда должны быть списком, User(id="00000000-0000-0000-0000-000000000001", roles=[auth_user, news_maker_role])

    app: CustomFastApi = request.app
    settings: Settings = app.get_settings()

    return (
        User(id=UUID("00000000-0000-0000-0000-000000000001"), roles=[admin_role])
        if settings.DEBUG
        else User(id=None, roles=[anonymous_role])
    )


CurrentUserDep = Annotated[User, Depends(get_user)]
