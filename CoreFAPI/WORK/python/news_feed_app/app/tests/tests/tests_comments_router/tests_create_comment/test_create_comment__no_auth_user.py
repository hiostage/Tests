from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_create_comment__no_auth_user(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Проверяет, что при попытке создать комментарий без авторизации API возвращает 403 Forbidden.

    Выполняется запрос на создание комментария к несуществующему посту от имени анонимного пользователя.
    Ожидается, что сервер отклонит запрос с кодом 403.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    """
    user = fake_anonymous_user
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            comment="comment",
        )
        response = await client.post(
            "/api/news/post/100/comment",
            json=data,
        )
        assert response.status_code == 403
