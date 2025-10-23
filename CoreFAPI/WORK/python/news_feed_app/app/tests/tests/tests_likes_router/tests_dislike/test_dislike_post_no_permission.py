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
async def test_dislike_post_no_permission(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует попытку удаления лайка без необходимых прав доступа.

    Шаги теста:
        1. Имитирует запрос от анонимного пользователя (без авторизации).
        2. Выполняет DELETE-запрос к API для удаления лайка.
        3. Проверяет, что сервер возвращает статус 403 Forbidden.

    Ожидаемый результат:
        - Пользователь без прав получает ошибку 403 при попытке удалить лайк.
        - Проверка выполняется без создания поста/лайка, так как ошибка должна возникать на этапе проверки прав.
    """

    fake_depends_list = [(get_user, fake_depends_async(fake_anonymous_user))]
    # Делаем запрос без создания поста, так как ожидаем 403 (Forbidden)
    async with override_dependency(app, fake_depends_list):

        response = await client.delete("/api/news/post/1/like")
        assert response.status_code == 403
