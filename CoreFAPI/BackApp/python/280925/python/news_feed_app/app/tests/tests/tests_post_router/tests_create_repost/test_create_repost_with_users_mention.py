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


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_repost_with_users_mention(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тестирует создание репоста с упоминанием пользователей и проверяет,
    что после успешного создания в очередь RabbitMQ отправляется корректное сообщение.

    Шаги теста:
    1. Создаётся исходный пост в базе данных.
    2. Формируется тело запроса для репоста с упоминаниями пользователей.
    3. С помощью override_dependency подменяется зависимость пользователя.
    4. Выполняется POST запрос на создание репоста.
    5. Проверяется успешный ответ API и наличие идентификатора репоста.
    6. Ожидается асинхронная обработка (2 секунды).
    7. Проверяется, что в RabbitMQ появилась задача с типом "mentioning_users",
       событием "create", соответствующим post_id и без comment_id.
    8. Проверяется, что упомянутые пользователи совпадают с ожидаемыми.

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

    users_mention = ["user1", "user2"]
    data_repost = {
        "title": "title repost",
        "content": f"Уважаемые @{users_mention[0]} и @{users_mention[1]} просьба...",
    }

    # Создадим репост
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(
            f"/api/news/post/{post.id}/repost", json=data_repost
        )
        assert response.status_code == 200
        response_data = response.json()
        repost_id = response_data["post"]["id"]
        assert repost_id

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="mentioning_users",
        type_mention="post",
        event_mention="create",
        post_id=repost_id,
        comment_id=None,
    )
    assert task
    assert set(task["usernames"]) == set(users_mention)
