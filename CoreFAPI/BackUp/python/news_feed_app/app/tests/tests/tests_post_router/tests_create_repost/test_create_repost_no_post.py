from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_repost_no_post(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует создание репоста на несуществующий пост.

    Выполняет POST-запрос на создание репоста с пустым телом запроса
    для поста с ID, которого нет в базе (100).
    Проверяет, что API корректно возвращает ошибку 404 Not Found.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """
    user = fake_news_maker_user
    # Попробуем создать репост на не существующий пост
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.post("/api/news/post/100/repost", json={})
        assert response.status_code == 404
