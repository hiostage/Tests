from typing import TYPE_CHECKING

import pytest
from database.models import Posts, Subscriptions
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
async def test_create_subscription_valid_data(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует успешное создание подписки пользователя на автора.

    Шаги теста:
    1. Создаёт пост автора в базе данных.
    2. Выполняет запрос на подписку пользователя на автора через API.
    3. Проверяет, что ответ успешный (HTTP 200).
    4. Проверяет, что подписка корректно сохранена в базе данных.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
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

    # Проверим запись в БД
    subscription_q = await session.execute(
        select(Subscriptions).where(
            Subscriptions.user_id == user.id, Subscriptions.author_id == author.id
        )
    )
    subscription = subscription_q.scalars().one_or_none()
    assert subscription
