from typing import TYPE_CHECKING

import pytest
from database.models import Subscriptions
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_get_exist_subscription(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует успешную проверку существующей подписки пользователя на автора.

    Шаги:
    1. Создаёт подписку пользователя на автора в базе данных.
    2. Выполняет GET-запрос для проверки подписки через API.
    3. Проверяет, что ответ успешный (HTTP 200).
    4. Проверяет, что в ответе поле "result" истинно (подписка существует).

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

    # Проверим существование подписки
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(
            "/api/news/subscription", params={"author_id": str(author.id)}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["result"]
