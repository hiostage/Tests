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
async def test_get_posts_by_filters__only_date_to(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует фильтрацию постов по конечной дате создания (date_to).

    Создаёт серию из 5 постов с датами создания от текущего момента до 4 дней назад.
    Выполняет запрос с фильтром `date_to`, установленным на дату 2 дня назад, и проверяет:
    - Возвращаются только посты, созданные ДО указанной даты включительно
    - Корректность количества возвращённых постов (3 шт.)
    - Соответствие ID возвращённых постов ожидаемым (последние 3 созданных поста)

    :param client: Асинхронный HTTP-клиент для тестирования эндпоинтов
    :param session: Сессия базы данных для создания тестовых данных
    :param app: Экземпляр приложения FastAPI с переопределёнными зависимостями
    """

    user = fake_news_maker_user
    # Создадим серию постов с разной датой
    count_posts = 5
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

    # Получим посты до позавчера включительно,
    # а значит (сегодня (-0), вчера(-1), позавчера(-2) (итого отнимаем -2 от сегодня))
    # ожидаем 3 поста (-4, -3, -2 дня назад)
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams(
            {
                "date_to": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "page": 1,
                "limit": 10,
            }
        )
        response = await client.get("/api/news/posts/filter", params=param)
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 3
        assert [post["id"] for post in data["posts"]] == [post.id for post in posts[2:]]
