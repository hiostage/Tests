import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import (
    fake_admin_user,
    fake_anonymous_user,
    fake_auth_user,
    fake_news_maker_user,
)

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_get_comment_by_id(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
     Тестирует получение комментария по ID.

    Шаги теста:
    1. Переопределяет зависимость FastAPI для пользователей.
    2. Отправляет GET-запрос на получение комментария.
    3. Проверяет успешный статус ответа.
    4. Проверяет, что данные комментария совпадают с отправленными.

    :param client: Тестовый клиент FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    :param app: Экземпляр приложения FastAPI.
    """
    users = [fake_auth_user, fake_anonymous_user, fake_news_maker_user, fake_admin_user]

    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    comment = Comments(post_id=post.id, comment="Test Comment", user_id=uuid.uuid4())
    session.add(comment)
    await session.commit()

    for user in users:
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            response = await client.get(f"/api/news/post/comment/{comment.id}")
            assert response.status_code == 200

        data = response.json()
        assert data["comment"]["comment"] == comment.comment
        assert data["comment"]["is_liked_by_me"] is False
