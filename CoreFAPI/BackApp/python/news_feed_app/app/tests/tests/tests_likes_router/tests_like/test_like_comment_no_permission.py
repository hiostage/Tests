from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_like_comment_no_permission(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует обработку запроса от неаутентифицированного пользователя.

    Шаги теста:
    1. Подмена зависимости аутентификации на анонимного пользователя
    2. Вызов эндпоинта POST /api/news/comment/1/like
    3. Проверка ответа 403 Forbidden

    Проверки:
    - Статус ответа 403
    - Система не выполняет поиск комментария до проверки прав
    """
    fake_depends_list = [(get_user, fake_depends_async(fake_anonymous_user))]
    # Делаем запрос без создания поста и комментария, так как ожидаем 403 (Forbidden)
    async with override_dependency(app, fake_depends_list):
        response = await client.post("/api/news/comment/1/like")
        assert response.status_code == 403
