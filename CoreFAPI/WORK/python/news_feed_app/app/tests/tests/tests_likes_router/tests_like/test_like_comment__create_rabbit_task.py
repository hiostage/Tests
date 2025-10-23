import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user
from tests.utils.utils import rabbit_task_search

if TYPE_CHECKING:
    from app_utils.rabbitmq_manager import RabbitMQClient
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_like_comment__create_rabbit_task(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    rabbitmq_client: "RabbitMQClient",
) -> None:
    """
    Тест проверяет создание лайка комментария и генерацию задачи в RabbitMQ.

    - Создаёт пост и комментарий к нему.
    - Отправляет запрос на лайк комментария.
    - Проверяет наличие задачи в RabbitMQ с параметрами:
      - type="new_like"
      - type_object="comment"
      - user_id лайкнувшего
      - post_id поста
      - author_id автора комментария
      - comment_id комментария
    """
    run_consumer(app)
    user = fake_auth_user
    # Создадим пост и комментарий к нему
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    comment = Comments(user_id=uuid.uuid4(), comment="comment")
    post.comments.append(comment)
    session.add(post)
    await session.commit()

    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Поставим лайк комментарию
    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/comment/{comment.id}/like")
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим задачу в RabbitMQ
    task = rabbit_task_search(
        rabbitmq_client,
        type="new_like",
        type_object="comment",
        user_id=str(user.id),
        post_id=post.id,
        author_id=str(comment.user_id),
        comment_id=comment.id,
    )
    assert task
