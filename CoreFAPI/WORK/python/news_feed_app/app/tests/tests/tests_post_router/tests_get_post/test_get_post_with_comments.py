import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_post_with_comments(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует получение поста с комментариями через API.

    Шаги теста:
        1. Создаёт пост с 5 комментариями.
        2. Выполняет GET-запрос к API.
        3. Проверяет статус ответа и счётчик комментариев.

    Проверки:
        - Статус ответа 200.
        - Количество комментариев (comments_count) соответствует созданным.
        - Анонимный доступ разрешён.

    :param client: Асинхронный HTTP-клиент (AsyncClient)
    :param session: Асинхронная сессия БД (AsyncSession)
    :param app: FastAPI приложение с зависимостями
    """
    # Создадим пост с комментами
    count_comments = 5
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    comments = [
        Comments(user_id=uuid.uuid4(), comment=f"Test Comment {i}")
        for i in range(count_comments)
    ]
    post.comments.extend(comments)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(comment.id) for comment in comments)

    # Выполним запрос
    fake_depends_list = [(get_user, fake_depends_async(fake_anonymous_user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(f"/api/news/post/{post_id}")
        assert response.status_code == 200
    data = response.json()
    assert data["post"]["comments_count"] == count_comments
