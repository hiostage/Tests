from contextlib import asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Sequence,
    TypeVar,
)

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi

T = TypeVar("T")


def fake_depends(fake_object: T) -> Callable[[], T]:
    """
    Функция принимает объект, который нужно вернуть из depends.

    :param fake_object: Ложный объект.
    :return: Callable[[], T].
    """

    def wrap() -> T:
        """
        Возвращает объект, подготовленный заранее.
        :return: Ложный объект.
        """
        return fake_object

    return wrap


def fake_depends_async(fake_object: T) -> Callable[[], Coroutine[Any, Any, T]]:
    """
    Функция принимает объект, который нужно асинхронно вернуть из depends.

    :param fake_object: Ложный объект.
    :return: Callable[[], T].
    """

    async def wrap() -> T:
        """
        Асинхронно возвращает объект, подготовленный заранее.
        :return: Ложный объект.
        """
        return fake_object

    return wrap


@asynccontextmanager
async def override_dependency(
    app: "CustomFastApi", dependency_mock: Sequence[tuple[Any, Any]]
) -> AsyncGenerator[None, None]:
    """
    Асинхронный контекстный менеджер для временной подмены зависимостей в FastAPI приложении.

    Позволяет временно заменить одну или несколько зависимостей на моки или заглушки.
    После завершения работы контекста все подмены автоматически очищаются.

    :param app: (CustomFastApi): Экземпляр FastAPI приложения, в котором нужно подменить зависимости.
    :param dependency_mock: (Sequence[tuple[Any, Any]]): Последовательность кортежей, где каждый кортеж содержит:
        - dependency: Зависимость, которую нужно подменить.
        - mock: Заглушка или мок, который будет использоваться вместо оригинальной зависимости.
    :yield: AsyncGenerator[None, None].

    Пример использования:
        async with override_dependency(app, [(get_db, get_mock_db), (get_user, get_mock_user)]):
            ...
    """
    for dependency, mock in dependency_mock:
        app.dependency_overrides[dependency] = mock
    try:
        yield
    finally:
        app.dependency_overrides.clear()
