import asyncio
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import AuthorWeight, Subscriptions
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
async def test_delete_subscription_update_weight_author(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует обновление веса автора при удалении подписки.

    Шаги теста:
    - Создаёт подписку пользователя на автора.
    - Выполняет запрос на удаление подписки.
    - Проверяет, что запрос выполнен успешно (HTTP 200).
    - Проверяет, что вес автора для пользователя после удаления подписки стал равен 0.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр тестового приложения FastAPI с переопределёнными зависимостями.
    :return: None
    """
    run_consumer(app)
    author = fake_news_maker_user
    user = fake_news_maker_user_2

    # Создадим подписку
    subscription = Subscriptions(user_id=user.id, author_id=author.id)
    session.add(subscription)
    # Вес не создаём, т.к. при создании подписки он будет создан автоматически (проверено тестами).
    await session.commit()

    # Отпишемся от автора.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(
            "/api/news/subscription", params={"author_id": str(author.id)}
        )
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим, что после отписки вес стал равен 0
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
    assert weight_author_for_current_user.weight == 0
