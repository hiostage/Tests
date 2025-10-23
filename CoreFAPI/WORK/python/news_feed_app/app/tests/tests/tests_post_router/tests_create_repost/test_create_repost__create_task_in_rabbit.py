import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import Posts, Subscriptions
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user
from tests.utils.utils import rabbit_task_search

if TYPE_CHECKING:
    from app_utils.rabbitmq_manager import RabbitMQClient
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_repost__create_task_in_rabbit(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тест проверяет создание репоста и генерацию задачи в RabbitMQ.

    - Запускает RabbitMQ consumer.
    - Создаёт оригинальный пост.
    - Создаёт подписки (subscribers) для пользователя.
    - Переопределяет зависимость FastAPI для аутентификации.
    - Отправляет запрос на создание репоста.
    - Проверяет успешный ответ.
    - Ждёт обработки фоновых задач.
    - Проверяет, что в RabbitMQ появилась задача с правильными параметрами:
      тип задачи, id автора, id репоста и список подписчиков.
    """
    run_consumer(app)
    # Создадим пост
    original_post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    session.add(original_post)
    # Создадим подписки
    user = fake_news_maker_user
    subscribers = [
        Subscriptions(author_id=user.id, user_id=uuid.uuid4()) for _ in range(3)
    ]
    session.add_all(subscribers)
    await session.commit()

    # Выполним запрос на создание репоста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            f"/api/news/post/{original_post.id}/repost", json={}
        )
        assert response.status_code == 200
        response_data = response.json()
    repost_id = response_data["post"]["id"]

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="new_post",
        author_id=str(user.id),
        post_id=repost_id,
    )
    assert task
    assert set(task["subscribers_ids"]) == set(
        str(subscriber.user_id) for subscriber in subscribers
    )
