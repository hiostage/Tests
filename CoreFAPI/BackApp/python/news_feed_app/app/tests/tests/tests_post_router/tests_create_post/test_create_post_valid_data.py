from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_post",
    [fake_news_maker_user, fake_admin_user],
)
@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_valid_data_no_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_post: "User",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание поста с валидными данными.

    Шаги теста:
    1. Переопределяет зависимость FastAPI для авторизации пользователя.
    2. Отправляет POST-запрос на создание поста с максимальной длиной заголовка и содержимого.
    3. Проверяет успешный статус ответа и получение ID созданного поста.
    4. Извлекает созданный пост из базы данных.
    5. Проверяет, что данные поста совпадают с отправленными.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param user_create_post: Пользователь, создающий пост (параметризованный).
    :param session: Сессия базы данных для выполнения операций.
    """

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_create_post))]
    # Создадим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="".join(choices(ascii_letters, k=MAX_TITLE_LENGTH)),
            content="".join(choices(ascii_letters, k=MAX_CONTENT_LENGTH)),
        )
        response = await client.post(
            "/api/news/post",
            json=data,
        )
        assert response.status_code == 200

        post_id = response.json()["post"]["id"]

    # Достаём из БД пост.
    post = await session.get(Posts, post_id)
    assert post
    assert post.title == data["title"]
    assert post.content == data["content"]
