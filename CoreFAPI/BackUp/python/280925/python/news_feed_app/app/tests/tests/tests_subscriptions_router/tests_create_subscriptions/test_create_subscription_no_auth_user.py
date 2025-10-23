from typing import TYPE_CHECKING

import pytest
from database.models import Subscriptions
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_create_subscription_no_auth_user(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует попытку создания подписки анонимным (неавторизованным) пользователем.
    Ожидается ошибка 403 Forbidden.

    Шаги:
    1. Отправляет запрос на подписку от имени анонимного пользователя.
    2. Проверяет, что сервер возвращает статус 403.
    3. Проверяет, что запись о подписке в базе данных не появилась.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    author = fake_news_maker_user
    user = fake_anonymous_user

    # Пробуем подписаться анонимным пользователем. Ожидаем 403
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            "/api/news/subscription", params={"author_id": str(author.id)}
        )
        assert response.status_code == 403

    # Проверим запись в БД
    subscription_q = await session.execute(
        select(Subscriptions).where(
            Subscriptions.user_id == user.id, Subscriptions.author_id == author.id
        )
    )
    subscription = subscription_q.scalars().one_or_none()
    assert not subscription
