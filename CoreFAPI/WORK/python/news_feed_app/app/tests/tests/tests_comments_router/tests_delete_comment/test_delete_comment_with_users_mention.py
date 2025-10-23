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
async def test_delete_comment_with_users_mention(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тестирует удаление комментария с упоминанием пользователей и проверяет,
    что после успешного удаления в очередь RabbitMQ отправляется корректное сообщение.

    В тесте:
    - Создаётся пост с комментарием, содержащим упоминания пользователей.
    - Удаляется комментарий через API.
    - Проверяется успешный ответ (HTTP 200).
    - После ожидания асинхронной обработки ищется сообщение в очереди RabbitMQ,
      соответствующее событию удаления комментария с нужными параметрами.
    - Проверяется корректность содержимого сообщения.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение.
    :param session: Асинхронная сессия базы данных.
    :param rabbitmq_client: Клиент RabbitMQ для проверки сообщений.
    """
    user = fake_news_maker_user
    # Создадим пост с комментарием
    post = Posts(user_id=uuid.uuid4(), title="test post", content="test content")
    users_mention = ["user1", "user2"]
    comment = Comments(
        user_id=fake_news_maker_user.id,
        comment=f"Уважаемые @{users_mention[0]} и @{users_mention[1]} просьба...",
    )
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id

    # Удалим комментарий
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"api/news/post/comment/{comment.id}")
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="mentioning_users",
        type_mention="comment",
        event_mention="delete",
        post_id=post.id,
        comment_id=comment.id,
    )
    assert task
    assert set(task["usernames"]) == set(users_mention)
