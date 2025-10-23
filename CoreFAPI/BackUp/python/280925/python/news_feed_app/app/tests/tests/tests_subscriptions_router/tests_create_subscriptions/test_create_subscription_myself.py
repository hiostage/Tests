from typing import TYPE_CHECKING

import pytest
from database.models import Subscriptions
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_create_subscription_myself(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует попытку подписаться на самого себя (ожидается ошибка 400).

    Шаги:
    1. Пытается создать подписку, где автор совпадает с пользователем.
    2. Проверяет, что сервер возвращает статус 400 (Bad Request).
    3. Проверяет, что в базе данных не появилась запись о подписке.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    user = fake_news_maker_user
    author_id = user.id

    # Пробуем подписаться на самого себя. Ожидаем 400.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            "/api/news/subscription", params={"author_id": str(author_id)}
        )
        assert response.status_code == 400

    # Проверим запись в БД
    subscription_q = await session.execute(
        select(Subscriptions).where(
            Subscriptions.user_id == user.id, Subscriptions.author_id == author_id
        )
    )
    subscription = subscription_q.scalars().one_or_none()
    assert not subscription
