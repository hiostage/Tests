from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize("user", [fake_auth_user, fake_anonymous_user])
@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_no_permission(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    user: "User",
) -> None:
    """
    Тестирует попытку создания репоста пользователями без соответствующих прав.

    Проверяется, что при попытке создать репост (даже на несуществующий пост)
    пользователи без разрешений (например, анонимные или с ограниченными правами)
    получают ошибку 403 Forbidden.

    :param client: Асинхронный HTTP-клиент для отправки запросов к API.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    :param session: Асинхронная сессия базы данных (не используется напрямую, но необходима для фикстуры).
    :param user: Пользователь, для которого проверяется доступ (параметризуется).
    """
    # Пробуем сделать репост пользователями, которым нельзя делать репост
    # Не создаём оригинальный пост, т.к ожидаем 403 (Forbidden)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Пробуем создать репост.
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            "/api/news/post/100/repost",
            json={},
        )
        assert response.status_code == 403
