import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.comments import MAX_COMMENT_LENGTH, Comments
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_comment, comment_text",
    [
        (fake_auth_user, ""),
        (fake_auth_user, "".join(choices(ascii_letters, k=MAX_COMMENT_LENGTH + 1))),
    ],
)
@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_create_comment_invalid_data(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_comment: "User",
    session: "AsyncSession",
    comment_text: str,
) -> None:
    """
    Проверяет, что при попытке обновить комментарий с пустым текстом или текстом,
    превышающим максимальную длину, API возвращает ошибку 422 Unprocessable Entity.

    Тест создаёт пост с комментарием, затем пытается обновить комментарий с некорректными данными.
    Проверяется, что запрос отклоняется с кодом 422, а текст комментария в базе не изменяется.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    :param user_create_comment: Пользователь, создавший комментарий.
    :param session: Асинхронная сессия базы данных для подготовки и проверки данных.
    :param comment_text: Текст комментария для теста (пустой или слишком длинный).
    """
    # Создадим пост с комментарием
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    comment = Comments(user_id=user_create_comment.id, comment="Test Comment")
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id
    comment_id = comment.id
    # Пробуем обновить
    fake_depends_list = [(get_user, fake_depends_async(user_create_comment))]
    async with override_dependency(app, fake_depends_list):
        new_comment = comment_text
        data = dict(
            comment=new_comment,
        )
        response = await client.patch(
            f"/api/news/post/comment/{comment_id}",
            json=data,
        )
        assert response.status_code == 422
    # Проверим в БД
    session.expunge_all()
    comment_in_bd = await session.get(Comments, comment_id)
    assert comment_in_bd
    assert comment_in_bd.comment != new_comment
