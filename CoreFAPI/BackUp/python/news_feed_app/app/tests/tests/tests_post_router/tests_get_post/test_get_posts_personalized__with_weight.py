import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import HashtagWeight, Posts
from database.models.hashtags import Hashtags
from dependencies.user import get_user
from httpx import QueryParams
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_posts_personalized__with_weight(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тест проверяет получение персонализированных постов с учётом веса.

    Логика:
    - Запускает consumer для обработки сообщений.
    - Создаёт 4 поста с разными пользователями и хэштегами.
    - Создаёт подписку текущего пользователя на первого автора.
    - Ставит лайк на последний пост.
    - Проверяет обновление веса хэштега у последнего поста.
    - Добавляет дополнительный вес хэштегу.
    - Запрашивает персонализированные посты и проверяет порядок и количество.
    """

    run_consumer(app)
    user = fake_news_maker_user
    # Создадим 4 поста
    posts = [
        Posts(
            user_id=uuid.uuid4(),
            title=f"post {i} user",
            content=f"content {i} user",
            hashtags=[Hashtags(name=f"#hashtag{i}")],
        )
        for i in range(4)
    ]
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)

    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        # Создадим подписку на 1-го пользователя
        response = await client.post(
            "/api/news/subscription", params={"author_id": str(posts[0].user_id)}
        )
        assert response.status_code == 200
        # Лайкнем последний пост
        response = await client.post(f"/api/news/post/{posts[-1].id}/like")
        assert response.status_code == 200

        await asyncio.sleep(2)
        # Достанем вес хештега у последнего поста
        weight_hashtag_q = await session.execute(
            select(HashtagWeight).where(
                HashtagWeight.user_id == user.id,
                HashtagWeight.hashtag_id == posts[-1].hashtags[0].id,
            )
        )
        weight_hashtag = weight_hashtag_q.scalars().one_or_none()
        assert weight_hashtag
        # Добавим ему веса
        weight_hashtag.weight += 40
        await session.commit()

        # Теперь сделаем запрос, ожидаем 2 поста, 1-й - это posts[0], 2-й - это posts[-1]
        param = QueryParams({"page": 1, "limit": 10})
        response = await client.get("/api/news/posts/personalized", params=param)
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) == 2
    assert data["posts"][0]["id"] == posts[0].id
    assert data["posts"][1]["id"] == posts[-1].id
