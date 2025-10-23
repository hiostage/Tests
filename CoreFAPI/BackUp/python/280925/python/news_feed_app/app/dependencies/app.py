from typing import Annotated

from core.classes.app import CustomFastApi
from fastapi import Depends, Request


def get_app(request: Request) -> CustomFastApi:
    """
    Получает экземпляр приложения CustomFastApi из объекта запроса FastAPI.

    :param request: Объект запроса FastAPI.
    :return: Экземпляр приложения CustomFastApi.
    """
    app: "CustomFastApi" = request.app
    return app  # noqa: PIE781


AppDep = Annotated[CustomFastApi, Depends(get_app)]
