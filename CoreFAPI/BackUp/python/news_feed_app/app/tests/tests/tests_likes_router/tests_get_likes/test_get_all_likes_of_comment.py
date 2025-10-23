import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Likes, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_get_all_likes_of_post(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Проверяет корректное получение лайков комментария с пагинацией.

    Тест создаёт пост с комментарием, к которому прикреплено 21 лайк.
    Затем запрашивает третью страницу лайков с лимитом 10 лайков.
    Ожидается, что:
    - общее количество страниц равно 3,
    - на третьей странице будет ровно 1 лайк.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    :param session: Асинхронная сессия базы данных для подготовки данных.
    """
    # Создадим пост, коммент и 21 лайк к нему
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    comment = Comments(user_id=uuid.uuid4(), comment="comment")
    post.comments.append(comment)
    likes = [Likes(user_id=uuid.uuid4()) for _ in range(21)]
    comment.likes.extend(likes)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id
    assert all(bool(like.id) for like in likes)

    fake_depends_list = [(get_user, fake_depends_async(fake_anonymous_user))]

    # Выполним запрос к 3 странице, ожидаем увидеть 1 лайк
    async with override_dependency(app, fake_depends_list):
        response = await client.get(
            f"/api/news/comment/{comment.id}/likes",
            params={"page": 3, "limit": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["likes"]) == 1
        assert data["count_pages"] == 3
