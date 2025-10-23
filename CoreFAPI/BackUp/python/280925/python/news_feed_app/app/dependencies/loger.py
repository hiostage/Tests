from typing import TYPE_CHECKING, Callable

from fastapi import Request  # noqa: TC002

if TYPE_CHECKING:
    from logging import Logger

    from core.classes.app import CustomFastApi


def get_loger(name: str) -> Callable[[Request], "Logger"]:
    """
    Функция принимает имя логера и вернёт функцию ожидающую Request.

    :param name: Имя.
    :return: Callable[[Request], Logger].
    """

    def wrapper(request: Request) -> "Logger":
        """
        Функция вернёт логер по заранее заданному имени.

        :param request: Request.
        :return: Logger.
        """
        app: "CustomFastApi" = request.app
        return app.get_logger(name)

    return wrapper
