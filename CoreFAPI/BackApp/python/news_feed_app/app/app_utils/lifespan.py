from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

from app_utils.start_func import (
    print_debug_banner,
    run_consumer,
    run_janitor,
)

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi


@asynccontextmanager
async def lifespan_func(app: "CustomFastApi") -> AsyncGenerator[None, None]:
    """
    lifespan_func функция, обычно выполняет что-то до и после запуска приложения.

    :param app: CustomFastApi.
    :return: AsyncGenerator[None, None].
    """
    if app.get_settings().DEBUG:
        print_debug_banner()

    log = app.get_logger("lifespan")

    run_janitor(app)  # Запускается сборщик мусора.
    run_consumer(app)  # Запускаем rabbit consumer
    try:
        log.info("Запускаем приложение.")
        yield  # Запускаем приложение.
    finally:

        log.info("Завершаю работу приложения.")
