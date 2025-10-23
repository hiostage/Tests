import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Subscriptions
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_get_exist_subscriptions(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует получение списка подписок с пагинацией.

    Шаги:
    1. Создаёт 21 подписку для пользователя (ожидается 3 страницы при лимите 10).
    2. Выполняет запрос к третьей странице с лимитом 10.
    3. Проверяет, что в ответе 1 подписка (последняя страница).
    4. Проверяет, что общее количество страниц равно 3.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """

    user = fake_news_maker_user_2

    # Создадим подписки
    # (21 подписку, ожидаем 3 страницы и 1 подписка на последней странице,
    # при лимите 10 подписок на страницу)
    subscriptions = [
        Subscriptions(user_id=user.id, author_id=uuid.uuid4()) for _ in range(21)
    ]
    session.add_all(subscriptions)
    await session.commit()

    # Выполним запрос
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(
            "/api/news/subscriptions", params={"page": 3, "limit": 10}
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["subscriptions"]) == 1
    assert data["count_pages"] == 3
