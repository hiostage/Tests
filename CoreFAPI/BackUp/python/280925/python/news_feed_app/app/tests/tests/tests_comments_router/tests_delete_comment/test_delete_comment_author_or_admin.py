import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_comment, user_delete_comment",
    [
        (fake_auth_user, fake_auth_user),
        (fake_auth_user, fake_admin_user),
    ],
)
@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_delete_post_author_or_admin(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_comment: "User",
    user_delete_comment: "User",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление комментария автором или администратором.

    Сценарии теста:
    1. Автор удаляет свой комментарий.
    2. Администратор удаляет комментарий другого пользователя.

    Шаги теста:
    1. Создание тестового поста.
    2. Авторизация пользователя для удаления комментария.
    3. Отправка DELETE-запроса на удаление комментария.
    4. Проверка успешного ответа (200 OK).
    5. Убедиться, что комментарий удален из базы данных.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param user_create_comment: Пользователь, прокомментировавший пост.
    :param user_delete_comment: Пользователь, удаляющий комментарий.
    :param session: Сессия базы данных для выполнения операций.
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
    comment_id = comment.id

    fake_depends_list = [(get_user, fake_depends_async(user_delete_comment))]

    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"api/news/post/comment/{comment.id}")
        assert response.status_code == 200

    session.expunge(comment)

    comment_in_bd = await session.get(Comments, comment_id)
    assert comment_in_bd is None
