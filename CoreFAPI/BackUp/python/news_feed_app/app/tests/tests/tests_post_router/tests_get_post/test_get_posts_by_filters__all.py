import uuid
from datetime import UTC, datetime, timedelta
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
async def test_get_posts_by_filters__all(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Комплексный тест фильтрации постов с использованием всех параметров фильтра.

    Создаёт несколько постов с различными характеристиками:
    - Два поста, которые должны пройти все фильтры (по дате, хештегам, пользователю, заголовку и содержимому)
    - Несколько постов, которые не должны попасть в результат из-за несоответствия одному или нескольким фильтрам

    Проверяет, что при запросе с комплексным набором фильтров возвращаются только ожидаемые посты.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param session: Асинхронная сессия базы данных для создания и сохранения тестовых данных.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    """
    user = fake_news_maker_user
    # Создадим серию постов, которые будут немного отличаться,
    # 2 из них будут нашей целью. Два, потому, что нужно будет проверить date_from вместе с date_to
    search_title = "search title"
    search_content = "search content"
    search_user = user.id
    search_date_from = datetime.now(UTC) - timedelta(days=2)
    search_date_to = datetime.now(UTC) - timedelta(days=1)
    search_hastags = ["#дом", "#огород"]

    # Создадим 2 поста (которые мы будем ожидать после фильтрации), за вчера и позавчера
    hastags_posts = [Hashtags(name=name) for name in search_hastags]
    post_1 = Posts(
        user_id=search_user,
        title=search_title,
        content=search_content,
        created_at=search_date_to,
    )
    post_1.hashtags.extend(hastags_posts)
    post_1.hashtags.append(Hashtags(name="#сад"))
    post_2 = Posts(
        user_id=search_user,
        title=search_title,
        content=search_content,
        created_at=search_date_from,
    )
    post_2.hashtags.extend(hastags_posts)

    # Создадим похожий, но с 1 хештегом
    post_3 = Posts(
        user_id=search_user,
        title=search_title,
        content=search_content,
        created_at=search_date_from,
    )
    post_3.hashtags.append(hastags_posts[0])

    # Создадим похожий, но за сегодня
    post_4 = Posts(
        user_id=search_user,
        title=search_title,
        content=search_content,
    )
    post_4.hashtags.extend(hastags_posts)

    # Создадим похожий, но с другим пользователем
    post_5 = Posts(
        user_id=uuid.uuid4(),
        title=search_title,
        content=search_content,
        created_at=search_date_from,
    )
    post_5.hashtags.extend(hastags_posts)

    # Создадим похожий, но за 3 дня назад
    post_6 = Posts(
        user_id=search_user,
        title=search_title,
        content=search_content,
        created_at=search_date_from - timedelta(days=1),
    )
    post_6.hashtags.extend(hastags_posts)

    # Создадим похожий, но с другим title
    post_7 = Posts(
        user_id=search_user,
        title="no",
        content=search_content,
        created_at=search_date_from,
    )
    post_7.hashtags.extend(hastags_posts)

    # Создадим похожий, но с другим content
    post_8 = Posts(
        user_id=search_user,
        title=search_title,
        content="no",
        created_at=search_date_from,
    )
    post_8.hashtags.extend(hastags_posts)

    posts = [post_1, post_2, post_3, post_4, post_5, post_6, post_7, post_8]
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)

    # Сделаем запрос, ожидаем увидеть только post_1 и post_2
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams(
            {
                "date_from": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "date_to": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "hashtags": search_hastags,
                "search_content": search_content,
                "search_title": search_title,
                "user_id": str(user.id),
                "page": 1,
                "limit": 10,
            }
        )
        response = await client.get("/api/news/posts/filter", params=param)
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 2
        assert {data["posts"][0]["id"], data["posts"][1]["id"]} == {
            post_1.id,
            post_2.id,
        }
