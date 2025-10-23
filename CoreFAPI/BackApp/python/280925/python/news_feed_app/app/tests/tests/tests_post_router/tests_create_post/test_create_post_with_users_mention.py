import asyncio
from typing import TYPE_CHECKING

import pytest
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
async def test_create_post_with_users_mention(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тестирует создание поста с упоминанием пользователей и проверяет,
    что после успешного создания в очередь RabbitMQ отправляется корректное сообщение.

    Шаги теста:
    1. Подмена зависимости пользователя для аутентификации.
    2. Создание поста с упоминаниями пользователей в контенте.
    3. Проверка успешного ответа API (HTTP 200).
    4. Ожидание асинхронной обработки и публикации сообщения в RabbitMQ.
    5. Получение и проверка сообщения из очереди RabbitMQ:
       - тип сообщения "mentioning_users",
       - тип упоминания "post",
       - событие "create",
       - упомянутые пользователи совпадают с ожидаемыми,
       - идентификатор поста корректен,
       - поле comment_id отсутствует (None).

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Экземпляр тестируемого приложения FastAPI.
    :param session: Асинхронная сессия базы данных.
    :param rabbitmq_client: Клиент RabbitMQ для проверки сообщений.
    """

    user = fake_news_maker_user
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Создадим пост.
    users_mention = ["user1", "user2"]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="title",
            content=f"Уважаемые @{users_mention[0]} и @{users_mention[1]} просьба...",
        )
        response = await client.post(
            "/api/news/post",
            json=data,
        )
        assert response.status_code == 200

    post_id = response.json()["post"]["id"]

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="mentioning_users",
        type_mention="post",
        event_mention="create",
        post_id=post_id,
        comment_id=None,
    )
    assert task
    assert set(task["usernames"]) == set(users_mention)
