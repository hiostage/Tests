import uuid
from typing import TYPE_CHECKING

import pytest
from app_utils.permission import news_maker_role
from database.models import Attachments
from dependencies.user import get_user
from schemas.users import User
from tests.utils.checks import has_records_in_bd
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_news_maker_user
from tests.utils.requests import client_delete_media, client_post_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.media_router
@pytest.mark.asyncio
async def test_delete_file_other_user(
    client: "AsyncClient", image_file: bytes, app: "CustomFastApi"
) -> None:
    """
    Тестирует попытку удаления файла другим пользователем с ролью news_maker.

    Шаги теста:
    1. Загрузка файла пользователем с ролью news_maker.
    2. Авторизация другого пользователя с ролью news_maker.
    3. Попытка удаления файла.
    4. Проверка статуса ответа (400 Bad Request).
    5. Верификация сохранения файла в базе данных.

    :param client: Тестовый клиент FastAPI
    :param image_file: Тестовый файл изображения
    :param app: Экземпляр приложения FastAPI
    """
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_news_maker_user))]
    # Добавим изображение.
    response = await client_post_media(app, fake_depends_list, client, image_file)
    assert response.status_code == 200
    media_id = response.json()["media"]["id"]

    # Создаём нового пользователя, который имеет права на медиа
    fake_news_maker_user_2 = User(id=uuid.uuid4(), roles=[news_maker_role])
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(fake_news_maker_user_2))]
    # Пробуем удалить изображение.
    response = await client_delete_media(app, fake_depends_list, client, media_id)
    assert response.status_code == 400

    # Проверяем, что БД есть запись.
    session_maker = app.get_db().get_session_fabric()
    async with session_maker() as session:
        assert await has_records_in_bd(Attachments, session)
