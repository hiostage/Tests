from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_delete_nonexistent_comment(
    client: "AsyncClient",
    app: "CustomFastApi",
) -> None:
    """
    Проверяет, что попытка удалить несуществующий комментарий возвращает 404 Not Found.

    Выполняется запрос на удаление комментария с несуществующим ID от имени администратора.
    Ожидается, что сервер вернёт статус 404.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    """
    user = fake_admin_user
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.delete("api/news/post/comment/100")
        assert response.status_code == 404
