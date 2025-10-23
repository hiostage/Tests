from typing import TYPE_CHECKING

import pytest
from database.models import Attachments
from dependencies.user import get_user
from tests.utils.checks import has_records_in_bd, has_records_in_minio
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.media_router
@pytest.mark.asyncio
async def test_create_upload_file_bad_image_file(
    client: "AsyncClient", fake_image_file: bytes, app: "CustomFastApi"
) -> None:
    """
    Проверяем роут добавления изображения.
    Ситуация: Прилетает файл, который притворяется картинкой.
    Ожидаем ошибку 400.
    Записи в БД и Minio не должны быть добавлены.

    :param client: AsyncClient.
    :param fake_image_file: bytes.
    :param app: CustomFastApi.
    :return: None.
    """

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_admin_user))]

    # Выполняем запрос.
    response = await client_post_media(app, fake_depends_list, client, fake_image_file)

    # Проверяем код ответа.
    assert response.status_code == 400

    # Проверяем, что запись в БД не добавлена (БД пуста).
    session_maker = app.get_db().get_session_fabric()
    async with session_maker() as session:
        assert not await has_records_in_bd(Attachments, session)

    # Проверяем, что запись в Minio не добавлена (Нет записей).
    assert not has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )
