from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from database.models import Attachments
from dependencies.db import get_session
from dependencies.user import get_user
from sqlalchemy.exc import SQLAlchemyError
from tests.utils.checks import has_records_in_bd, has_records_in_minio
from tests.utils.fake_depends import fake_depends, fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.media_router
@pytest.mark.asyncio
async def test_create_upload_file_raise_in_bd(
    client: "AsyncClient", image_file: bytes, app: "CustomFastApi"
) -> None:
    """
    Проверяем роут добавления изображения.
    Ситуация: При работе с БД неожиданно возникло исключение.
    Имитируем исключение в session.flush (SQLAlchemyError).
    Записи в БД и Minio не должны быть добавлены.

    :param client: AsyncClient.
    :param image_file: bytes.
    :param app: CustomFastApi.
    :return: None.
    """

    # Создаем мок сессии
    mock_session = AsyncMock()
    mock_session.add = MagicMock()

    # Настраиваем side_effect для метода flush
    mock_session.flush.side_effect = SQLAlchemyError("sqlalchemy: Что-то пошло не так")

    # Переопределяем зависимости в FastAPI
    fake_depends_list = [
        (get_user, fake_depends_async(fake_admin_user)),
        (get_session, fake_depends(mock_session)),
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
