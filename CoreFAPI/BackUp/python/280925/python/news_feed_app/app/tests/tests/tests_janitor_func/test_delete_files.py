import asyncio
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_janitor
from database.models import Attachments
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.checks import has_records_in_minio
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_delete_media, client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.janitor_func
@pytest.mark.asyncio
async def test_delete_files(
    client: "AsyncClient",
    image_file: bytes,
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление файлов через сборщик мусора.
    Файлы помечены как удалённые.

    Шаги теста:
    1. Проверка пустоты MinIO.
    2. Загрузка и удаление файла через клиент.
    3. Проверка наличия файла в MinIO после удаления.
    4. Запуск сборщика мусора и его ожидание.
    5. Проверка пустоты MinIO после работы сборщика.
    6. Проверка удаления вложения из БД.

    :param client: Тестовый клиент FastAPI
    :param image_file: Тестовый файл изображения
    :param app: Экземпляр приложения FastAPI
    :param session: Асинхронная сессия базы данных
    """
    # Убедимся, что minio пуста
    assert not has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )
    # Запишем и удалим вложение через клиент.

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_admin_user))]

    # Выполняем запрос.
    response = await client_post_media(app, fake_depends_list, client, image_file)
    assert response.status_code == 200
    id_attachment = response.json()["media"]["id"]
    response = await client_delete_media(app, fake_depends_list, client, id_attachment)
    assert response.status_code == 200

    # Убедимся, что minio не пуста
    assert has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )

    # Запускаем сборщика мусора, не обращаем внимание на интервал,
    # так как при запуске он сразу выполняет очистку, а только потом засыпает.
    run_janitor(app)  # Запускается сборщик мусора.
    await asyncio.sleep(0.1)  # Даем время на выполнение

    # Убедимся, что minio пуста
    assert not has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )

    # Убедимся, attachment удалён.
    attachment_q = await session.execute(
        select(Attachments).where(Attachments.id == id_attachment)
    )
    attachment = attachment_q.scalars().one_or_none()
    assert not attachment
