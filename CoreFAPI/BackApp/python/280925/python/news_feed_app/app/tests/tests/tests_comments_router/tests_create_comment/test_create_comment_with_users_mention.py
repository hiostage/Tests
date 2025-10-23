import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user
from tests.utils.utils import rabbit_task_search

if TYPE_CHECKING:
    from app_utils.rabbitmq_manager import RabbitMQClient
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_create_comment_with_users_mention(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тестирует создание комментария с упоминанием пользователей и проверяет,
    что после успешного создания в очередь RabbitMQ отправляется корректное сообщение.

    Шаги теста:
    1. Создаётся пост для привязки комментария.
    2. Создаётся комментарий с упоминаниями пользователей в тексте.
    3. Проверяется успешный ответ API (HTTP 200).
    4. Ожидается асинхронная обработка и публикация сообщения в RabbitMQ.
    5. Получается сообщение из очереди RabbitMQ и проверяется его содержимое:
       - тип сообщения "mentioning_users",
       - тип упоминания "comment",
       - событие "create",
       - упомянутые пользователи совпадают с ожидаемыми,
       - идентификатор поста и комментария корректны.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Экземпляр тестируемого приложения FastAPI.
    :param session: Асинхронная сессия базы данных.
    :param rabbitmq_client: Клиент RabbitMQ для проверки сообщений.
    """
    user = fake_news_maker_user
    # Создадим пост
    post = Posts(user_id=uuid.uuid4(), title="test post", content="test content")
    session.add(post)
    await session.commit()
    assert post.id

    # Создадим комментарий
    users_mention = ["user1", "user2"]
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            comment=f"Уважаемые @{users_mention[0]} и @{users_mention[1]} просьба...",
        )
        response = await client.post(
            f"/api/news/post/{post.id}/comment",
            json=data,
        )
        assert response.status_code == 200

        comment_id = response.json()["comment"]["id"]

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="mentioning_users",
        type_mention="comment",
        event_mention="create",
        post_id=post.id,
        comment_id=comment_id,
    )
    assert task
    assert set(task["usernames"]) == set(users_mention)
