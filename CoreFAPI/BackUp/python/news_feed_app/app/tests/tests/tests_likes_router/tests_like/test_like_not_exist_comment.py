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
async def test_like_not_exist_comment(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тестирование попытки лайка несуществующего комментария.

    Шаги:
    1. Подмена аутентификации на валидного пользователя
    2. Вызов POST для несуществующего комментария (ID=100)
    3. Проверка ответа 404 и сообщения об ошибке
    """
    fake_depends_list = [(get_user, fake_depends_async(fake_auth_user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.post("/api/news/comment/100/like")
        assert response.status_code == 404
