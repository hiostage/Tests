import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Likes, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_like_comment_invalid(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует обработку дублирующегося лайка на комментарии.

    Шаги теста:
    1. Создание тестовых данных:
       - Пост с комментарием
       - Лайк от тестового пользователя
    2. Попытка повторного лайка через API
    3. Проверка ошибки 400 Bad Request
    """
    user = fake_auth_user

    # Создадим пост, коммент к нему и лайк от нашего пользователя.
    post = Posts(user_id=uuid.uuid4(), title="test", content="test")
    comment = Comments(user_id=uuid.uuid4(), comment="test")
    like = Likes(user_id=user.id)
    comment.likes.append(like)
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id
    assert like.id

    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Пробуем поставить лайк ещё раз, ожидаем 400
    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/comment/{comment.id}/like")
        assert response.status_code == 400
