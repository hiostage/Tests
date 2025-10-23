from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from database.models import Attachments
from dependencies.minio import get_minio_manager
from dependencies.user import get_user
from minio.error import MinioException
from tests.utils.checks import has_records_in_bd, has_records_in_minio
from tests.utils.fake_depends import (
    fake_depends,
    fake_depends_async,
)
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.media_router
@pytest.mark.asyncio
async def test_create_upload_file_raise_in_minio(
    client: "AsyncClient", image_file: bytes, app: "CustomFastApi"
) -> None:
    """
    Проверяем роут добавления изображения.
    Ситуация: При работе с Minio неожиданно возникло исключение.
    Имитируем исключение в minio_manager.save_file (MinioException).
    Записи в БД и Minio не должны быть добавлены.

    :param client: AsyncClient.
    :param image_file: bytes.
    :param app: CustomFastApi.
    :return: None.
    """
    mock_minio_manager = MagicMock()
    mock_minio_manager.get_file_url.return_value = "/path/to/file"
    mock_minio_manager.save_file.side_effect = MinioException(
        "Minio: Что-то пошло не так."
    )

    # Переопределяем зависимости в FastAPI
    fake_depends_list = [
        (get_user, fake_depends_async(fake_admin_user)),
        (get_minio_manager, fake_depends(mock_minio_manager)),
    ]

    # Выполняем запрос.
    response = await client_post_media(app, fake_depends_list, client, image_file)
    assert response.status_code == 500

    # Проверяем, что запись в БД не добавлена (БД пуста).
    session_maker = app.get_db().get_session_fabric()
    async with session_maker() as session:
        assert not await has_records_in_bd(Attachments, session)

    # Проверяем, что запись в Minio не добавлена (Нет записей).
    assert not has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )
