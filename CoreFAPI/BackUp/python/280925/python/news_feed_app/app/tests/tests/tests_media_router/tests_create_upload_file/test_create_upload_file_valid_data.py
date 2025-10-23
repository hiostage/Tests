from typing import TYPE_CHECKING

import pytest
from database.models import Attachments
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.media_router
@pytest.mark.asyncio
async def test_create_upload_file_valid_data(
    client: "AsyncClient", image_file: bytes, app: "CustomFastApi"
) -> None:
    """
    Проверяем роут добавления изображения.
    Ожидаем запись в БД и MinIO.

    :param client: AsyncClient.
    :param image_file: bytes.
    :param app: CustomFastApi.
    :return: None.
    """
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_admin_user))]

    # Выполняем запрос.
    response = await client_post_media(app, fake_depends_list, client, image_file)
    # Проверяем код ответа.
    assert response.status_code == 200

    # Проверяем запись в БД.
    id_attachment = response.json()["media"]["id"]
    assert id_attachment

    session_maker = app.get_db().get_session_fabric()
    async with session_maker() as session:
        attachment = await session.get(Attachments, id_attachment)
    assert attachment

    # Проверяем запись в MinIO
    minio_client = app.get_minio_client()
    filename = str(attachment.attachment_path).split("/")[-1]
    obj = minio_client.stat_object(
        app.get_settings().MINIO_SETTINGS.MINIO_BUCKET, filename
    )
    assert obj
