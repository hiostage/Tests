from typing import TYPE_CHECKING

import pytest
from database.models import Posts
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
async def test_get_posts_page_limit(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует пагинацию постов с ограничением по количеству на страницу.

    Создаёт 21 пост от одного пользователя и проверяет корректность работы пагинации
    при лимите 10 постов на страницу. Ожидается, что всего будет 3 страницы, а на третьей
    странице будет только 1 пост.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param session: Асинхронная сессия базы данных для создания и сохранения тестовых данных.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """
    user = fake_news_maker_user
    # Создадим 21 пост, будем выводить по 10 постов на страницу, ожидаем всего 3 страницы, на 3 странице 1 пост
    count_post = 21
    posts = [
        Posts(
            user_id=user.id,
            title=f"post {i}",
            content=f"content {i}",
        )
        for i in range(count_post)
    ]
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)

    # Выполним запрос по пользователю и 3-ю страницу (лимит 10 на страницу),
    # ожидаем в ответе 1 пост, а также общее количество страниц 3
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams({"user_id": str(user.id), "page": 3, "limit": 10})
        response = await client.get("/api/news/posts/filter", params=param)
        assert response.status_code == 200
        data = response.json()
        assert data["count_pages"] == 3
        assert len(data["posts"]) == 1
