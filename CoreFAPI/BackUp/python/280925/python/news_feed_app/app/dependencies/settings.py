from typing import TYPE_CHECKING, Annotated

from core.classes.settings import Settings
from fastapi import Depends

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from fastapi import Request


def get_settings(request: "Request") -> Settings:
    """
    Возвращает настройки приложения.

    :param request: Request.
    :return: Settings.
    """
    app: "CustomFastApi" = request.app
    return app.get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
