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
async def test_dislike_not_exist_comment(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тестирование удаления лайка с несуществующего комментария.

    Шаги:
    1. Подмена аутентификации на валидного пользователя
    2. Вызов DELETE /api/news/comment/100/like (комментарий 100 не существует)
    3. Проверка ответа 404
    """

    fake_depends_list = [(get_user, fake_depends_async(fake_auth_user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.delete("/api/news/comment/100/like")
        assert response.status_code == 404
