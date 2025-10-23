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
async def test_get_posts_by_filters__only_search_content(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует фильтрацию постов по поиску подстроки в контенте.

    Создаёт несколько постов с разным содержимым, в котором встречается слово "post"
    в разных регистрах и позициях. Затем выполняет запрос с фильтром `search_content`,
    проверяя, что возвращаются только посты, содержимое которых содержит искомую подстроку,
    без учёта регистра.

    В данном тесте поиск по слову "PoSt" должен вернуть 3 поста.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param session: Асинхронная сессия базы данных для создания и сохранения тестовых данных.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """

    user = fake_news_maker_user
    # Создадим серию постов с разным контентом (в 3 будет наше слово `post`)
    posts = [
        Posts(
            user_id=user.id,
            title="title",
            content="dfgdfg post",
        ),
        Posts(
            user_id=user.id,
            title="title",
            content="dfgdfg PosTdfgdfg",
        ),
        Posts(
            user_id=user.id,
            title="title",
            content="dfgdfg tdfgdfg",
        ),
        Posts(
            user_id=user.id,
            title="title",
            content=" poSt tdfgdfg",
        ),
    ]
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)

    # Получим посты с поиском в контенте слова `post`, ожидаем 3 поста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams(
            {
                "search_content": " PoSt ",
                "page": 1,
                "limit": 10,
            }
        )
        response = await client.get("/api/news/posts/filter", params=param)
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 3
        assert all("post" in post["content"].lower() for post in data["posts"])
