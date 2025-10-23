import asyncio
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import HashtagWeight, Likes, Posts
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
async def test_dislike_post_update_weight_hashtags(
    client: "AsyncClient", app: "CustomFastApi", session: "AsyncSession"
) -> None:
    """
    Тестирует обновление веса хештегов при удалении лайка с поста.

    Шаги теста:
    - Создаёт пост с хештегами и лайком пользователя.
    - Выполняет запрос на удаление лайка.
    - Проверяет, что запрос выполнен успешно (HTTP 200).
    - Проверяет, что вес каждого хештега для пользователя после удаления лайка стал равен 0.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param app: Экземпляр тестового приложения FastAPI с переопределёнными зависимостями.
    :param session: Асинхронная сессия базы данных.
    :return: None
    """
    run_consumer(app)
    author = fake_news_maker_user
    user = fake_news_maker_user_2
    # Создадим пост с хештегами и с лайком (вес хештегов будет создан автоматически)
    post = Posts(user_id=author.id, title="title", content="content")
    like = Likes(user_id=user.id)
    hashtags = [Hashtags(name=f"#hashtag_{i}") for i in range(3)]
    post.hashtags.extend(hashtags)
    post.likes.append(like)
    session.add(post)
    await session.commit()
    assert post.id
    assert like.id
    assert all(bool(tag.id) for tag in hashtags)

    # Уберём лайк с поста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{like.post_id}/like")
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим, что вес хештегов изменился и равен 0
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
    assert all(weight_hashtag.weight == 0 for weight_hashtag in weight_hashtags_in_bd)
