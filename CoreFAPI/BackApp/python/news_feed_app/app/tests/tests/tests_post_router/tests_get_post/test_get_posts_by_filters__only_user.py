from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from httpx import QueryParams
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_posts_by_filters__only_user(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует фильтрацию постов по user_id.

    Проверяет, что при фильтрации по конкретному пользователю возвращаются только его посты.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param session: Асинхронная сессия базы данных для создания и коммита тестовых данных.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """
    # Создадим посты от двух пользователей
    user_1 = fake_news_maker_user
    user_2 = fake_news_maker_user_2
    users = [user_1, user_2]
    count_posts = 3
    posts_user_1 = [
        Posts(user_id=user_1.id, title=f"post {i} user1", content=f"content {i} user1")
        for i in range(count_posts)
    ]
    posts_user_2 = [
        Posts(user_id=user_2.id, title=f"post {i} user2", content=f"content {i} user2")
        for i in range(count_posts)
    ]
    session.add_all([*posts_user_1, *posts_user_2])
    await session.commit()
    assert all(bool(post.id) for post in posts_user_1)
    assert all(bool(post.id) for post in posts_user_2)

    # Будем делать запрос от лица user_1 (хотя это и не важно)
    fake_depends_list = [(get_user, fake_depends_async(user_1))]
    # Получим новости, фильтруя их по user_id
    async with override_dependency(app, fake_depends_list):
        for user in users:
            param = QueryParams({"user_id": str(user.id), "page": 1, "limit": 10})
            response = await client.get("/api/news/posts/filter", params=param)
            assert response.status_code == 200
            data = response.json()
            assert len(data["posts"]) == count_posts
            assert all(post["user_id"] == str(user.id) for post in data["posts"])
