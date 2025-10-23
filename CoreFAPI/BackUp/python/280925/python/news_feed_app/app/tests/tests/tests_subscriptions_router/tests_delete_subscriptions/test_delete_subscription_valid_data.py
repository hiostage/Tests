from typing import TYPE_CHECKING

import pytest
from database.models import Subscriptions
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
async def test_delete_subscription_valid_data(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует успешное удаление подписки пользователя на автора.

    Шаги:
    1. Создаёт подписку пользователя на автора в базе данных.
    2. Выполняет запрос DELETE для отписки пользователя от автора через API.
    3. Проверяет, что ответ сервера успешный (HTTP 200).
    4. Проверяет, что подписка удалена из базы данных.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    author = fake_news_maker_user
    user = fake_news_maker_user_2

    # Создадим подписку
    subscription = Subscriptions(user_id=user.id, author_id=author.id)
    session.add(subscription)
    await session.commit()
    assert subscription.created_at

    # Отпишемся от автора.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(
            "/api/news/subscription", params={"author_id": str(author.id)}
        )
        assert response.status_code == 200

    # Проверим, что подписка удалена.
    session.expunge_all()

    subscription_in_bd_q = await session.execute(
        select(Subscriptions).where(
            Subscriptions.user_id == user.id, Subscriptions.author_id == author.id
        )
    )
    subscription_in_bd = subscription_in_bd_q.scalars().one_or_none()
    assert subscription_in_bd is None
