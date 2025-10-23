from datetime import UTC, datetime, timedelta
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
async def test_get_posts_by_filters__sorted_by_date(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует корректность сортировки постов по дате создания в порядке убывания.

    Создаёт несколько постов одного пользователя с разницей во времени создания в несколько дней.
    Затем выполняет запрос к API с фильтрацией по user_id и проверяет, что возвращённые посты
    отсортированы от самых новых к самым старым по полю `created_at`.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param session: Асинхронная сессия базы данных для создания и сохранения тестовых данных.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """
    # создадим посты с разницей в 1 день
    user = fake_news_maker_user
    count_posts = 3
    posts = [
        Posts(
            user_id=user.id,
            title=f"post {i} user",
            content=f"content {i} user",
            created_at=datetime.now(UTC) - timedelta(days=i),
        )
        for i in range(count_posts)
    ]
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)

    # Получим эти посты с фильтрацией по пользователю
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):

        param = QueryParams({"user_id": str(user.id), "page": 1, "limit": 10})
        response = await client.get("/api/news/posts/filter", params=param)
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == count_posts
        date1 = datetime.fromisoformat(data["posts"][0]["created_at"].replace("Z", ""))
        date2 = datetime.fromisoformat(data["posts"][1]["created_at"].replace("Z", ""))
        date3 = datetime.fromisoformat(data["posts"][2]["created_at"].replace("Z", ""))
        assert date1 > date2 > date3
