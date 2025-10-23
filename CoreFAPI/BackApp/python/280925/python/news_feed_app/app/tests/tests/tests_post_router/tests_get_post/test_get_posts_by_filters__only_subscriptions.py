import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts, Subscriptions
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
async def test_get_posts_by_filters__only_subscriptions(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует получение постов с фильтром по подпискам.

    Шаги:
    1. Создаёт 3 авторов с уникальными UUID.
    2. Подписывает пользователя на первых двух авторов.
    3. Создаёт по одному посту от каждого автора.
    4. Выполняет запрос к эндпоинту с фильтром `subscriptions=True`.
    5. Проверяет, что возвращается ровно 2 поста от авторов, на которых пользователь подписан.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    user = fake_news_maker_user
    authors_ids = [uuid.uuid4() for _ in range(3)]

    # Подпишем пользователя на первых 2-х авторов
    subscriptions = [
        Subscriptions(user_id=user.id, author_id=author_id)
        for author_id in authors_ids[:2]
    ]

    # Создадим по посту от каждого автора
    posts = [
        Posts(user_id=author_id, title="title", content="content")
        for author_id in authors_ids
    ]

    session.add_all([*subscriptions, *posts])
    await session.commit()

    # Выполним запрос с фильтрацией только авторов, на которых подписан текущий пользователь.
    # Ожидаем 2 поста.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams(
            {
                "subscriptions": True,
                "page": 1,
                "limit": 10,
            }
        )
        response = await client.get("/api/news/posts/filter", params=param)
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) == 2
    assert set(post["user_id"] for post in data["posts"]) == set(
        str(author_id) for author_id in authors_ids[:2]
    )
