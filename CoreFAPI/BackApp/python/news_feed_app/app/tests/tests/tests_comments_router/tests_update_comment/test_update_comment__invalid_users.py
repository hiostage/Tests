import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import (
    fake_anonymous_user,
    fake_auth_user,
    fake_news_maker_user,
    fake_news_maker_user_2,
)

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_update_comment__invalid_users(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Проверяет, что пользователи, не являющиеся автором комментария или администратором,
    не могут обновить комментарий.

    Тест создаёт пост с комментарием от user_creation_comment, затем пытается обновить
    комментарий от имени пользователей из списка bad_users. Ожидается, что сервер
    вернёт статус 403 Forbidden, а текст комментария в базе останется неизменным.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    :param session: Асинхронная сессия базы данных для подготовки и проверки данных.
    """
    user_creation_comment = fake_news_maker_user
    bad_users = [fake_anonymous_user, fake_auth_user, fake_news_maker_user_2]

    # Создадим пост с комментарием
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    comment = Comments(user_id=user_creation_comment.id, comment="Test Comment")
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id
    comment_id = comment.id

    for user in bad_users:
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            new_comment = f"new comment {user.id}"
            data = dict(
                comment=new_comment,
            )
            response = await client.patch(
                f"/api/news/post/comment/{comment_id}",
                json=data,
            )
            assert response.status_code == 403

            # Проверим в БД
            session.expunge_all()
            comment_in_bd = await session.get(Comments, comment_id)
            assert comment_in_bd
            assert comment_in_bd.comment != new_comment
