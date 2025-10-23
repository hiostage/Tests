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


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_create_subscription_create_weight_author(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует корректное создание записи веса автора.

    Шаги теста:
    - Создаёт пост от имени автора.
    - Выполняет запрос на подписку пользователя на автора.
    - Проверяет, что запрос выполнен успешно (HTTP 200).
    - Проверяет, что в таблице AuthorWeight для пары (пользователь-автор)
      существует запись с весом, равным константе WEIGHT_BONUS.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр тестового приложения FastAPI.
    :return: None
    """
    WEIGHT_BONUS = 100
    run_consumer(app)
    author = fake_news_maker_user
    user = fake_news_maker_user_2
    # Создадим пост в БД.
    post = Posts(user_id=author.id, title="title", content="content")
    session.add(post)
    await session.commit()
    assert post.id

    # Подпишемся на автора поста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            "/api/news/subscription", params={"author_id": str(author.id)}
        )
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим, что вес автора для пользователя существует и равен WEIGHT_BONUS
    weight_author_for_current_user_q = await session.execute(
        select(AuthorWeight).where(
            AuthorWeight.user_id == user.id, AuthorWeight.author_id == author.id
        )
    )
    weight_author_for_current_user = (
        weight_author_for_current_user_q.scalars().one_or_none()
    )
    assert weight_author_for_current_user
    assert weight_author_for_current_user.weight == WEIGHT_BONUS
