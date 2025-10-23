import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
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
async def test_create_comment__create_task_in_rabbit(
    client: "AsyncClient",
    app: "CustomFastApi",
    rabbitmq_client: "RabbitMQClient",
    session: "AsyncSession",
) -> None:
    """
    Тест проверяет создание комментария и публикацию события нового комментария в RabbitMQ.

    Логика:
    - Создаёт пост с новым user_id.
    - Отправляет запрос на создание комментария от тестового пользователя.
    - Проверяет успешный ответ и получение ID комментария.
    - Ждёт обработки сообщений.
    - Проверяет наличие задачи (события) в RabbitMQ с правильными параметрами.
    """
    run_consumer(app)
    user = fake_news_maker_user
    # Создадим пост
    post = Posts(user_id=uuid.uuid4(), title="test post", content="test content")
    session.add(post)
    await session.commit()
    assert post.id

    # Создадим комментарий
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            comment="comment",
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
        type="new_comment",
        author_id=str(post.user_id),
        user_id=str(user.id),
        comment_id=comment_id,
        post_id=post.id,
    )
    assert task
