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
async def test_like_post_no_permission(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует попытку постановки лайка без необходимых прав доступа.

    Шаги теста:
        1. Имитирует запрос от анонимного пользователя (без авторизации).
        2. Выполняет POST-запрос к API для добавления лайка.
        3. Проверяет, что сервер возвращает статус 403 Forbidden.

    Ожидаемый результат:
        - Пользователь без прав получает ошибку 403 при попытке поставить лайк.
        - Проверка выполняется без создания поста, так как ошибка должна возникать на этапе проверки прав.
    """
    fake_depends_list = [(get_user, fake_depends_async(fake_anonymous_user))]
    # Делаем запрос без создания поста, так как ожидаем 403 (Forbidden)
    async with override_dependency(app, fake_depends_list):

        response = await client.post("/api/news/post/1/like")
        assert response.status_code == 403
