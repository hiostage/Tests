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
async def test_dislike_comment_valid(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирование успешного удаления лайка с комментария.

    Шаги:
    1. Создание тестовых данных:
       - Пост с комментарием
       - Лайк текущего пользователя
    2. Вызов DELETE /api/news/comment/{comment_id}/like
    3. Проверка успешного ответа (200 OK)
    4. Верификация отсутствия лайка в БД

    Проверки:
    - Статус ответа 200
    - Лайк удалён из базы данных
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
    like_id = like.id

    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Убираем свой лайк
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/comment/{comment.id}/like")
        assert response.status_code == 200

    # Забудем всё
    session.expunge_all()

    # Убедимся, что лайк удалён
    like_in_bd = await session.get(Likes, like_id)
    assert not like_in_bd
