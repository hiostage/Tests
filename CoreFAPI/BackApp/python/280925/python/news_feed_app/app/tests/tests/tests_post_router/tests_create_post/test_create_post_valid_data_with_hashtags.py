from typing import TYPE_CHECKING, Sequence

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from database.models.hashtags import Hashtags
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_valid_data_with_hashtags(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тест создания поста с валидными данными и хэштегами.

    :param client: Клиент для отправки запросов
    :param app: Приложение FastAPI
    :param session: Сессия базы данных

    Процесс:
    1. Подменяет зависимости для получения фейкового пользователя.
    2. Создаёт пост с валидными данными и хэштегами.
    3. Проверяет статус ответа (должен быть 200 OK).
    4. Извлекает ID созданного поста из ответа.
    5. Получает созданный пост из базы данных.
    6. Проверяет соответствие данных поста:
       - Заголовок
       - Содержание
       - Хэштеги
    """
    user = fake_news_maker_user
    tags_names = ["#tag1", "#tag2"]
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Создадим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="Test Post",
            content="Test Content",
            hashtag_names=tags_names,
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
    assert post.hashtags
    hashtags: Sequence["Hashtags"] = post.hashtags
    assert set(tags_names) == set(tag.name for tag in hashtags)
