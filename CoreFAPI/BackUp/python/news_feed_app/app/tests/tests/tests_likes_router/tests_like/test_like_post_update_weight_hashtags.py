import asyncio
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import HashtagWeight, Posts
from database.models.hashtags import Hashtags
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_like_post_update_weight_hashtags(
    client: "AsyncClient", app: "CustomFastApi", session: "AsyncSession"
) -> None:
    """
    Тестирует обновление веса хештегов при лайке поста, если вес уже существует.

    Шаги теста:
    - Создаёт пост с набором хештегов.
    - Создаёт существующие записи веса для каждого хештега с некоторым значением delta_weight.
    - Выполняет запрос на лайк поста от имени пользователя.
    - Проверяет, что запрос выполнен успешно (HTTP 200).
    - Проверяет, что вес каждого хештега увеличился на HASHTAG_WEIGHT_BONUS.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param app: Экземпляр тестового приложения FastAPI с переопределёнными зависимостями.
    :param session: Асинхронная сессия базы данных.
    :return: None
    """
    HASHTAG_WEIGHT_BONUS = 1
    run_consumer(app)
    delta_weight = 20
    author = fake_news_maker_user
    user = fake_news_maker_user_2
    # Создадим пост с хештегами в БД.
    post = Posts(user_id=author.id, title="title", content="content")
    hashtags = [Hashtags(name=f"#hashtag_{i}") for i in range(3)]
    post.hashtags.extend(hashtags)
    session.add(post)
    await session.flush()
    assert post.id
    assert all(bool(tag.id) for tag in hashtags)
    # Создадим существующий вес
    weight_hashtags = [
        HashtagWeight(hashtag_id=tag.id, weight=delta_weight, user_id=user.id)
        for tag in hashtags
    ]
    session.add_all(weight_hashtags)
    await session.commit()

    # Лайкнем пост
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/post/{post.id}/like")
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим, что вес хештегов изменился и равен HASHTAG_WEIGHT_BONUS + delta_weight
    session.expunge_all()
    hashtags_ids = [tag.id for tag in hashtags]
    weight_hashtags_q = await session.execute(
        select(HashtagWeight).where(
            HashtagWeight.hashtag_id.in_(hashtags_ids), HashtagWeight.user_id == user.id
        )
    )

    weight_hashtags_in_bd = weight_hashtags_q.scalars().all()
    assert weight_hashtags_in_bd
    assert len(weight_hashtags_in_bd) == len(hashtags)
    assert all(
        weight_hashtag.weight == HASHTAG_WEIGHT_BONUS + delta_weight
        for weight_hashtag in weight_hashtags_in_bd
    )
