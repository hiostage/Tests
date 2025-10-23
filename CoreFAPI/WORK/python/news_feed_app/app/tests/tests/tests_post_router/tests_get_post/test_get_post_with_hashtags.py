import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_post_with_hashtags(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует получение поста с хэштегами через API для разных пользователей.

    Шаги теста:
        1. Создаёт пост с 3 хэштегами.
        2. Для каждого пользователя выполняет GET-запрос к API.
        3. Проверяет статус ответа и список хэштегов.

    Проверки:
        - Статус ответа 200 для всех пользователей.
        - Список хэштегов в ответе соответствует созданным.
        - Наличие полного набора тегов.

    :param client: Асинхронный HTTP-клиент (AsyncClient)
    :param app: FastAPI приложение с зависимостями
    :param session: Асинхронная сессия БД (AsyncSession)
    """
    users = [fake_auth_user, fake_anonymous_user]

    # Создадим пост с хэштегами
    hashtags = [Hashtags(name=f"#tag_{i}") for i in range(3)]
    tags_names = [tag.name for tag in hashtags]
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    post.hashtags.extend(hashtags)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(tag.id) for tag in hashtags)

    for user in users:
        # Выполним запрос
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            response = await client.get(f"/api/news/post/{post_id}")
            assert response.status_code == 200

    # Проверим полученные данные последнего.
    data = response.json()
    assert data["post"]["hashtag_names"]
    assert set(data["post"]["hashtag_names"]) == set(tags_names)
