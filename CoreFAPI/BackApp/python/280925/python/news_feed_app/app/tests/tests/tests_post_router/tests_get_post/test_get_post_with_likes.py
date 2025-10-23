import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Likes, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_post_with_likes(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует получение поста с информацией о лайках и статусе лайка текущего пользователя.

    Шаги теста:
        1. Создаётся пост с одним лайком от пользователя `user_liked`.
        2. Пост сохраняется в базе данных.
        3. Запрос к API выполняется дважды:
            - с авторизацией текущего пользователя `user_liked` (должен видеть, что лайк поставлен).
            - с другим пользователем `user_not_liked` (должен видеть, что лайк не поставлен).

    Проверки:
        - Статус ответа 200.
        - В ответе `likes_count` равен 1.
        - Поле `is_liked_by_me` корректно отражает статус лайка для текущего пользователя.

    :param client: HTTP клиент для тестирования API.
    :param session: Асинхронная сессия базы данных.
    :param app: Инстанс FastAPI.
    """
    user_liked = fake_news_maker_user
    user_not_liked = fake_news_maker_user_2
    # Создадим пост с лайком
    like = Likes(user_id=user_liked.id)
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    post.likes.append(like)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert like.id

    # Получим пост пользователем, который поставил лайк.
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_liked))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(f"/api/news/post/{post_id}")
        assert response.status_code == 200

    data = response.json()
    assert data["post"]["likes_count"] == 1
    assert data["post"]["is_liked_by_me"] is True

    # Получим пост пользователем, который НЕ поставил лайк.
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_not_liked))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(f"/api/news/post/{post_id}")
        assert response.status_code == 200

    data = response.json()
    assert data["post"]["likes_count"] == 1
    assert data["post"]["is_liked_by_me"] is False
