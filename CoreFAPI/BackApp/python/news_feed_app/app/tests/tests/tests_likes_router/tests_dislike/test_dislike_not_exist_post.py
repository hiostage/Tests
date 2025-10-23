from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_dislike_not_exist_post(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тест удаления лайка для несуществующего поста.

    :param client: Клиент для отправки запросов
    :param app: Приложение FastAPI
    """
    fake_depends_list = [(get_user, fake_depends_async(fake_auth_user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.delete("/api/news/post/100/like")
        assert response.status_code == 404
