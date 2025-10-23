from typing import TYPE_CHECKING

import pytest
from app_utils.minio_manager import MinioManager
from database.models import Attachments
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.checks import has_records_in_minio
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.minio_manager
@pytest.mark.asyncio
async def test_bulk_delete_files(
    client: "AsyncClient",
    image_file: bytes,
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует массовое удаление файлов через MinioManager.

    Шаги теста:
    1. Создает 3 тестовых файла через API
    2. Проверяет наличие записей в БД
    3. Удаляет файлы через MinioManager.bulk_delete_files()
    4. Проверяет отсутствие файлов в MinIO

    :param client: Тестовый клиент FastAPI
    :param image_file: Бинарные данные тестового изображения
    :param app: Экземпляр приложения
    :param session: Сессия БД для проверки данных
    """

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_admin_user))]
    # Добавим 3 изображения через клиент.
    for _ in range(3):
        response = await client_post_media(app, fake_depends_list, client, image_file)
        assert response.status_code == 200

    # Проверим, что создано 3 записи в БД:
    attachments_q = await session.execute(select(Attachments))
    attachments = attachments_q.scalars().all()
    assert len(attachments) == 3

    # Удалим массово файлы через MinioManager
    m_manager = MinioManager(
        settings=app.get_settings(), minio_client=app.get_minio_client()
    )
    errors = await m_manager.bulk_delete_files(
        [att.attachment_path for att in attachments]
    )
    assert len(list(errors)) == 0

    # Убедимся, что файлы удалены.
    assert not has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )
