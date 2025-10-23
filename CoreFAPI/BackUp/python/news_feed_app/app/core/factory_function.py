from typing import TYPE_CHECKING, Any, Callable, Sequence, Type

from core.classes.app import CustomFastApi

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

    from core.classes.settings import Settings
    from fastapi import APIRouter, Request


def get_app(
    settings: "Settings",
    lifespan: Callable[[CustomFastApi], "AbstractAsyncContextManager[None]"],
    routers: Sequence["APIRouter"],
    exception_handlers: Sequence[tuple[Type[Any], Callable[["Request", Any], Any]]],
) -> CustomFastApi:
    """
    Функция базово настраивает FastAPI и возвращает приложение.

    :param settings: Настройки приложения.
    :param lifespan: Менеджер контекста для выполнения чего-либо до и после запуска приложения.
    :param routers: Последовательность из подключаемых роутерах.
    :param exception_handlers: Последовательность из подключаемых хендлерах исключений. Пример: [(Exception, exception_handler_func)]
    """
    if settings.DEBUG:
        app = CustomFastApi(settings=settings, lifespan=lifespan)
    else:
        app = CustomFastApi(
            settings=settings,
            lifespan=lifespan,
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
        )
    for router in routers:
        app.include_router(router=router, prefix="/api")
    for exception_handler in exception_handlers:
        app.add_exception_handler(*exception_handler)

    return app
