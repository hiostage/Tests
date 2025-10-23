import asyncio
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import AuthorWeight, Posts
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
async def test_like_post_update_weight_author(
    client: "AsyncClient", app: "CustomFastApi", session: "AsyncSession"
) -> None:
    """
    Тестирует обновление веса автора при лайке поста пользователем.

    Шаги теста:
    - Создаёт пост от имени автора.
    - Создаёт существующую запись веса автора для пользователя с некоторым значением delta_weight.
    - Выполняет запрос на лайк поста от имени пользователя.
    - Проверяет, что запрос выполнен успешно (HTTP 200).
    - Проверяет, что вес автора для пользователя увеличился на AUTHOR_WEIGHT_BONUS.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param app: Экземпляр тестового приложения FastAPI.
    :param session: Асинхронная сессия базы данных.
    :return: None
    """
    AUTHOR_WEIGHT_BONUS = 1
    run_consumer(app)
    delta_weight = 20
    author = fake_news_maker_user
    user = fake_news_maker_user_2
    # Создадим пост в БД.
    post = Posts(user_id=author.id, title="title", content="content")
    session.add(post)
    # Создадим вес автора для пользователя
    weight_author = AuthorWeight(
        user_id=user.id, author_id=author.id, weight=delta_weight
    )
    session.add(weight_author)
    await session.commit()
    assert post.id

    # Лайкнем пост
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/post/{post.id}/like")
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим, что вес автора для пользователя изменился и равен AUTHOR_WEIGHT_BONUS + delta_weight
    session.expunge_all()
    weight_author_for_current_user_q = await session.execute(
        select(AuthorWeight).where(
            AuthorWeight.user_id == user.id, AuthorWeight.author_id == author.id
        )
    )
    weight_author_for_current_user = (
        weight_author_for_current_user_q.scalars().one_or_none()
    )
    assert weight_author_for_current_user
    assert weight_author_for_current_user.weight == AUTHOR_WEIGHT_BONUS + delta_weight
