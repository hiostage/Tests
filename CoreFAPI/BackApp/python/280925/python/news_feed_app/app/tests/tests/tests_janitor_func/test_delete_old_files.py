import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_janitor
from database.models import Attachments
from dependencies.user import get_user
from sqlalchemy import update
from tests.utils.checks import has_records_in_minio
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.janitor_func
@pytest.mark.asyncio
async def test_delete_old_files(
    client: "AsyncClient",
    image_file: bytes,
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление старых (не привязанных к посту) файлов через сборщик мусора.

    Шаги теста:
    1. Загрузка файла через клиент.
    2. Перенос вложения в прошлое, чтобы оно считалось старым.
    3. Запуск сборщика мусора.
    4. Проверка удаления файла из MinIO и БД.

    :param client: Тестовый клиент FastAPI
    :param image_file: Тестовый файл изображения
    :param app: Экземпляр приложения FastAPI
    :param session: Асинхронная сессия базы данных
    """
    # Запишем вложение через клиент.
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_admin_user))]

    # Выполняем запрос.
    response = await client_post_media(app, fake_depends_list, client, image_file)
    assert response.status_code == 200
    id_attachment = response.json()["media"]["id"]

    # Перенесём вложение за рамки времени
    delta = app.get_settings().JANITOR_SETTINGS.CONSIDER_OLD_FILE + timedelta(
        seconds=10
    )
    new_created_at = datetime.now() - delta
    await session.execute(
        update(Attachments)
        .where(Attachments.id == id_attachment)
        .values(created_at=new_created_at)
    )
    await session.commit()

    # Запускаем сборщика мусора, не обращаем внимание на интервал,
    # так как при запуске он сразу выполняет очистку, а только потом засыпает.
    run_janitor(app)
    await asyncio.sleep(0.1)  # Даем время на выполнение

    # Убедимся, что minio пуста
    assert not has_records_in_minio(
        app.get_minio_client(), app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    )

    # Убедимся, attachment удалён.
    attachment_in_bd = await session.get(Attachments, id_attachment)
    assert not attachment_in_bd
