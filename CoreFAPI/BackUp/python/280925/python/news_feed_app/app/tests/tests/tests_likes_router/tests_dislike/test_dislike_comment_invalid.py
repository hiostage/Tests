import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_dislike_comment_invalid(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирование удаления несуществующего лайка с комментария.

    Шаги:
    1. Создание тестовых данных (пост + комментарий)
    2. Подмена аутентификации текущего пользователя
    3. Вызов DELETE /api/news/comment/{comment_id}/like
    4. Проверка ошибки 400
    """

    user = fake_auth_user

    # Создадим пост и коммент к нему.
    post = Posts(user_id=uuid.uuid4(), title="test", content="test")
    comment = Comments(user_id=uuid.uuid4(), comment="test")
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id

    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Пробуем убрать несуществующий лайк
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/comment/{comment.id}/like")
        assert response.status_code == 400
