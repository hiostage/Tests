import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.comments import MAX_COMMENT_LENGTH
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_comment, comment",
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
    comment: str,
) -> None:
    """
    Проверяет, что при попытке создать комментарий с пустым текстом или текстом,
    превышающим максимальную длину, API возвращает статус 422 (Unprocessable Entity).

    Создаёт тестовый пост, затем пытается добавить к нему некорректный комментарий
    от имени тестового пользователя с помощью переопределения зависимостей.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param app: Тестируемое FastAPI приложение.
    :param user_create_comment: Пользователь, от имени которого создаётся комментарий.
    :param session: Асинхронная сессия базы данных для подготовки тестовых данных.
    :param comment: Текст комментария для теста (пустой или слишком длинный).
    """
    user_create_post = uuid.uuid4()
    post = Posts(user_id=user_create_post, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id

    fake_depends_list = [(get_user, fake_depends_async(user_create_comment))]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            comment=comment,
        )
        response = await client.post(
            f"/api/news/post/{post.id}/comment",
            json=data,
        )
        assert response.status_code == 422
