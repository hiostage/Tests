from typing import TYPE_CHECKING, Any, Sequence

from tests.utils.fake_depends import override_dependency

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from httpx._models import Response


async def client_post_media(
    app: "CustomFastApi",
    dependency_mock: Sequence[tuple[Any, Any]],
    client: "AsyncClient",
    image_file: bytes,
) -> "Response":
    """
    Функция-помощник для выполнения POST-запроса к медиа-роуту для создания картинки.
    Используется в тестах, чтобы избежать дублирования кода.

    :param app: (CustomFastApi): Экземпляр FastAPI приложения, в котором нужно подменить зависимости.
    :param dependency_mock: (Sequence[tuple[Any, Any]]): Последовательность кортежей, где каждый кортеж содержит:
        - dependency: Зависимость, которую нужно подменить.
        - mock: Заглушка или мок, который будет использоваться вместо оригинальной зависимости.
    :param client: Асинхронный HTTP-клиент (AsyncClient) для выполнения запросов.
    :param image_file: Байтовое представление изображения, которое будет отправлено в запросе.

    :return: Ответ от сервера (Response).
    """
    async with override_dependency(app, dependency_mock):
        # Отправляем POST-запрос с файлом
        response = await client.post(
            "/api/news/media/image",
            files={"file": ("image.jpg", image_file, "image/jpeg")},
            params={"caption": "Фото"},
        )
    return response


async def client_delete_media(
    app: "CustomFastApi",
    dependency_mock: Sequence[tuple[Any, Any]],
    client: "AsyncClient",
    media_id: int,
) -> "Response":
    """
    Функция-помощник для выполнения DELETE-запроса к медиа-роуту для удаления картинки.
    Используется в тестах, чтобы избежать дублирования кода.

    :param app: (CustomFastApi): Экземпляр FastAPI приложения, в котором нужно подменить зависимости.
    :param dependency_mock: (Sequence[tuple[Any, Any]]): Последовательность кортежей, где каждый кортеж содержит:
        - dependency: Зависимость, которую нужно подменить.
        - mock: Заглушка или мок, который будет использоваться вместо оригинальной зависимости.
    :param client: Асинхронный HTTP-клиент (AsyncClient) для выполнения запросов.
    :param media_id: ID картинки.

    :return: Ответ от сервера (Response).
    """
    async with override_dependency(app, dependency_mock):
        # Отправляем DELETE-запрос
        response = await client.delete(
            "/api/news/media/image",
            params={"media_id": media_id},
        )
    return response
