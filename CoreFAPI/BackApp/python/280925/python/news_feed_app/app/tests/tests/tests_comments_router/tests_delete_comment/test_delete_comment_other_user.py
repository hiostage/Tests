import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import (
    fake_anonymous_user,
    fake_auth_user,
    fake_news_maker_user_2,
)

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_comment, user_delete_comment",
    [
        (fake_auth_user, fake_anonymous_user),
        (fake_auth_user, fake_news_maker_user_2),
    ],
)
@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_delete_comment_other_user(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_comment: "User",
    user_delete_comment: "User",
    session: "AsyncSession",
) -> None:
    """
    Проверяет, что пользователь не может удалить комментарий другого пользователя.

    Тест выполняет следующие шаги:
    1. Создает пост и комментарий от имени первого пользователя.
    2. Пытается удалить комментарий от имени другого пользователя.
    3. Проверяет, что сервер возвращает статус 403 Forbidden.
    4. Убеждается, что комментарий остался в базе данных.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    :param user_create_comment: Пользователь, создавший комментарий.
    :param user_delete_comment: Пользователь, пытающийся удалить комментарий.
    :param session: Асинхронная сессия базы данных для подготовки и проверки данных.
    """

    user_create_post = uuid.uuid4()
    post = Posts(user_id=user_create_post, title="Test Post", content="Test Content")
    session.add(post)
    await session.flush()
    comment = Comments(
        post_id=post.id, user_id=user_create_comment.id, comment="Test Comment"
    )
    session.add(comment)
    await session.commit()

    assert comment.id

    fake_depends_list = [(get_user, fake_depends_async(user_delete_comment))]

    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"api/news/post/comment/{comment.id}")
        assert response.status_code == 403

    session.expunge_all()
    # Проверим, что коммент на месте
    comment_in_bd = await session.get(Comments, comment.id)
    assert comment_in_bd
