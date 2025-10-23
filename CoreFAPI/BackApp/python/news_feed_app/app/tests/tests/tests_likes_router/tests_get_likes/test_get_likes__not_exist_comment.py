from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_get_likes__not_exist_comment(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Проверяет, что при запросе лайков к несуществующему комментарию API возвращает 404 Not Found.

    Выполняется GET-запрос к маршруту получения лайков с несуществующим ID комментария.
    Используется фиктивный пользователь с правами администратора.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    """
    user = fake_admin_user
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Выполним запрос к несуществующему комменту
    async with override_dependency(app, fake_depends_list):
        response = await client.get(
            "/api/news/comment/100/likes",
            params={"page": 1, "limit": 10},
        )
        assert response.status_code == 404
