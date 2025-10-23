import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Likes, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_get_comment_by_id__with_like(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Проверяет получение комментария по ID с информацией о лайке текущего пользователя.

    Тест создаёт пост с комментарием, к которому текущий пользователь поставил лайк.
    Затем выполняется запрос на получение комментария, и проверяется, что статус ответа 200,
    а в данных присутствует поле `is_liked_by_me` со значением True.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param session: Асинхронная сессия базы данных для подготовки тестовых данных.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    """
    user = fake_news_maker_user

    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    comment = Comments(user_id=uuid.uuid4(), comment="Test Comment")
    post.comments.append(comment)
    like = Likes(user_id=user.id)
    comment.likes.append(like)
    session.add(post)
    await session.commit()

    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(f"/api/news/post/comment/{comment.id}")
        assert response.status_code == 200

    data = response.json()
    assert data["comment"]["is_liked_by_me"] is True
