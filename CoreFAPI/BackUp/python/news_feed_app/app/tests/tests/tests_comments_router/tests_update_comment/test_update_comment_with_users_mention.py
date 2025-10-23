import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
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
async def test_update_comment_with_users_mention(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тестирует обновление комментария с упоминанием пользователей и проверяет,
    что после успешного обновления в очередь RabbitMQ отправляется корректное сообщение.

    Шаги теста:
    1. Создание поста с комментарием.
    2. Обновление текста комментария с упоминаниями пользователей.
    3. Проверка успешного ответа API (HTTP 200).
    4. Ожидание асинхронной обработки и публикация сообщения в RabbitMQ.
    5. Получение и проверка сообщения из очереди RabbitMQ:
       - тип сообщения "mentioning_users",
       - тип упоминания "comment",
       - событие "update",
       - идентификаторы поста и комментария корректны,
       - упомянутые пользователи совпадают с ожидаемыми.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Экземпляр тестируемого приложения FastAPI.
    :param session: Асинхронная сессия базы данных.
    :param rabbitmq_client: Клиент RabbitMQ для проверки сообщений.
    """
    user = fake_news_maker_user
    # Создадим пост с комментарием
    post = Posts(user_id=uuid.uuid4(), title="test post", content="test content")
    comment = Comments(
        user_id=fake_news_maker_user.id,
        comment="comment",
    )
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id

    users_mention = ["user1", "user2"]
    # Обновим комментарий
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        new_comment = f"Уважаемые @{users_mention[0]} и @{users_mention[1]} просьба..."
        data = dict(
            comment=new_comment,
        )
        response = await client.patch(
            f"/api/news/post/comment/{comment.id}",
            json=data,
        )
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="mentioning_users",
        type_mention="comment",
        event_mention="update",
        post_id=post.id,
        comment_id=comment.id,
    )
    assert task
    assert set(task["usernames"]) == set(users_mention)
