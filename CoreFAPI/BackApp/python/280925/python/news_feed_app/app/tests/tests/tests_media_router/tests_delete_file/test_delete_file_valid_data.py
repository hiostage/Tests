from typing import TYPE_CHECKING

import pytest
from database.models import Attachments
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user, fake_news_maker_user
from tests.utils.requests import client_delete_media, client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "mock_user_save, mock_user_delete",
    [
        (fake_news_maker_user, fake_news_maker_user),
        (fake_news_maker_user, fake_admin_user),
    ],
)
@pytest.mark.media_router
@pytest.mark.asyncio
async def test_delete_file_valid_data(
    client: "AsyncClient",
    image_file: bytes,
    app: "CustomFastApi",
    mock_user_save: "User",
    mock_user_delete: "User",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление файла с валидными данными.

    Параметризованные сценарии:
    1. Автор файла удаляет его.
    2. Администратор удаляет файл.

    Шаги теста:
    1. Загрузка файла пользователем.
    2. Авторизация пользователя для удаления файла.
    3. Удаление файла.
    4. Проверка успешного ответа (200 OK).
    5. Верификация, что вложение помечено как удаленное.

    :param client: Тестовый клиент FastAPI
    :param image_file: Тестовый файл изображения
    :param app: Экземпляр приложения FastAPI
    :param mock_user_save: Пользователь, загружающий файл
    :param mock_user_delete: Пользователь, удаляющий файл
    :param session: Асинхронная сессия базы данных
    """

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(mock_user_save))]
    # Добавим изображение.
    response = await client_post_media(app, fake_depends_list, client, image_file)
    assert response.status_code == 200
    media_id = response.json()["media"]["id"]

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(mock_user_delete))]
    # Удалим изображение.
    response = await client_delete_media(app, fake_depends_list, client, media_id)
    assert response.status_code == 200

    # Проверяем, что вложение помечено как удалённое
    attachment = await session.get(Attachments, media_id)
    assert attachment
    assert attachment.is_deleted
