import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_post_by_id(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует получение поста по идентификатору через API для разных типов пользователей.

    Шаги теста:
        1. Создаётся новый пост в базе данных.
        2. Для каждого пользователя выполняется GET-запрос к API по ID поста.
        3. Проверяется статус ответа и содержимое поста.

    Проверки:
        - Статус ответа 200.
        - Заголовок и содержимое поста соответствуют созданным данным.

    :param client: HTTP клиент для тестирования API.
    :param session: Асинхронная сессия базы данных.
    :param app: Инстанс FastAPI.
    """
    users = [fake_auth_user, fake_anonymous_user]

    # Создадим пост
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()

    for user in users:
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            response = await client.get(f"/api/news/post/{post.id}")
            assert response.status_code == 200

        # Проверим полученные данные.
        data = response.json()
        assert data["post"]["title"] == post.title
        assert data["post"]["content"] == post.content
