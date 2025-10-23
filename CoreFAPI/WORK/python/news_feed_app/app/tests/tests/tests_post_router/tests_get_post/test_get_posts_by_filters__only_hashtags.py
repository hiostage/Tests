from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags
from dependencies.user import get_user
from httpx import QueryParams
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_posts_by_filters__only_hashtags(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует фильтрацию постов по хештегам.

    Создаёт три поста с разными наборами хештегов и проверяет, что при фильтрации
    по нескольким хештегам возвращаются только те посты, которые содержат все указанные хештеги.

    В данном тесте фильтрация по хештегам `#дом` и `#сад` должна вернуть два поста:
    первый (с хештегами `#дом` и `#сад`) и третий (с тремя хештегами).

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param session: Асинхронная сессия базы данных для создания и сохранения тестовых данных.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """
    # Создадим посты с хештегами
    user = fake_news_maker_user
    posts = [
        Posts(user_id=user.id, title=f"post {i}", content=f"content {i}")
        for i in range(3)
    ]
    hashtags = [Hashtags(name="#дом"), Hashtags(name="#сад"), Hashtags(name="#огород")]
    posts[0].hashtags.extend([hashtags[0], hashtags[1]])
    posts[1].hashtags.extend([hashtags[1], hashtags[2]])
    posts[2].hashtags.extend(hashtags)
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)
    assert all(bool(hashtag.id) for hashtag in hashtags)

    # Отфильтруем посты по хештегам (#дом, #сад), ожидаем 2 поста posts[0] и posts[2]
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams({"hashtags": ["#дом", "#сад"], "page": 1, "limit": 10})
        response = await client.get("/api/news/posts/filter", params=param)
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 2
        assert set(post["id"] for post in data["posts"]) == {posts[0].id, posts[2].id}
