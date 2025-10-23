import asyncio
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2
from tests.utils.utils import rabbit_task_search

if TYPE_CHECKING:
    from app_utils.rabbitmq_manager import RabbitMQClient
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_create_subscription_valid_data(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тест проверяет успешное создание подписки и публикацию события нового подписчика в RabbitMQ.

    Логика:
    - Создаёт автора и пользователя.
    - Создаёт пост автора в базе.
    - Выполняет запрос на подписку пользователя на автора.
    - Проверяет успешный ответ.
    - Ждёт обработки сообщений.
    - Проверяет наличие задачи (события) в очереди RabbitMQ с правильными параметрами.
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

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="new_subscriber",
        author_id=str(author.id),
        subscriber_id=str(user.id),
    )
    assert task
