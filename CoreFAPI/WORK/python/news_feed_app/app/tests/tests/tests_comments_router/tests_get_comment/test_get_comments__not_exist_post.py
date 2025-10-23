from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from httpx import QueryParams
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_get_comments__not_exist_post(
    client: "AsyncClient", app: "CustomFastApi"
) -> None:
    """
    Проверяет, что при запросе комментариев к несуществующему посту API возвращает 404 Not Found.

    Выполняется GET-запрос к маршруту получения комментариев с несуществующим ID поста.
    Используется фиктивный пользователь с правами администратора.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    """
    user = fake_admin_user
    # Запросим 1-ю страницу несуществующего поста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams({"page": 1, "limit": 10})
        response = await client.get("/api/news/post/100/comments", params=param)
    assert response.status_code == 404
