import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from database.models.comments import MAX_COMMENT_LENGTH
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_comment",
    [fake_auth_user, fake_admin_user],
)
@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_create_comment_valid_data(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_comment: "User",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание комментария с валидными данными.

    Шаги теста:
    1. Переопределяет зависимость FastAPI для авторизации пользователя.
    2. Отправляет POST-запрос на создание комментария с максимальной длиной содержимого.
    3. Проверяет успешный статус ответа и получение ID созданного комментария.
    4. Извлекает созданный комментарий из базы данных.
    5. Проверяет, что данные комментария совпадают с отправленными.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param user_create_comment: Пользователь, создающий комментарий (параметризованный).
    :param session: Сессия базы данных для выполнения операций.
    """
    user_create_post = uuid.uuid4()
    post = Posts(user_id=user_create_post, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id

    fake_depends_list = [(get_user, fake_depends_async(user_create_comment))]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            comment="".join(choices(ascii_letters, k=MAX_COMMENT_LENGTH)),
        )
        response = await client.post(
            f"/api/news/post/{post.id}/comment",
            json=data,
        )
        assert response.status_code == 200

        comment_id = response.json()["comment"]["id"]

    # Достаём из БД пост.
    comment = await session.get(Comments, comment_id)
    assert comment
