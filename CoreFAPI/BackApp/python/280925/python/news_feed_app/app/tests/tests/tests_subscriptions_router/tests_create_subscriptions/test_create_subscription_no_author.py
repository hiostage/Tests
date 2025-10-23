import uuid
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
async def test_create_subscription_no_author(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Тестирует попытку создания подписки на несуществующего автора (ожидается 404).

    Шаги:
    1. Генерирует случайный UUID автора, которого нет в базе.
    2. Отправляет POST запрос на подписку на этого автора.
    3. Проверяет, что получен код ответа 404.
    4. Убеждается, что запись о подписке не была создана в базе данных.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param session: Асинхронная сессия базы данных.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    user = fake_news_maker_user
    author_id = uuid.uuid4()

    # Подпишемся на автора, у которого нет ни одного поста (т.е. мы не знаем о его существовании), ожидаем 404.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            "/api/news/subscription", params={"author_id": str(author_id)}
        )
        assert response.status_code == 404

    # Проверим запись в БД
    subscription_q = await session.execute(
        select(Subscriptions).where(
            Subscriptions.user_id == user.id, Subscriptions.author_id == author_id
        )
    )
    subscription = subscription_q.scalars().one_or_none()
    assert not subscription
