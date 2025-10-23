from typing import TYPE_CHECKING

import pytest
from database.models import Posts
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


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_other_user(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует запрет обновления поста сторонними пользователями через PATCH-запрос.

    **Проверки:**

    Статус 403 при попытке обновления:
      - Создателем другого поста
      - Обычным авторизованным пользователем
      - Анонимом

    :param client: Асинхронный HTTP-клиент (AsyncClient)
    :param app: FastAPI приложение с CustomFastAPI-расширениями
    :param session: Асинхронная сессия SQLAlchemy (AsyncSession)
    """
    user_create_post = fake_news_maker_user
    users_update_post = [fake_news_maker_user_2, fake_auth_user, fake_anonymous_user]

    # Создадим user_create_post простой пост
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id

    for user_update_post in users_update_post:
        # Переопределяем зависимость FastAPI (на user_update_post)
        fake_depends_list = [(get_user, fake_depends_async(user_update_post))]
        # Пробуем обновить пост.
        async with override_dependency(app, fake_depends_list):
            data = dict(
                title="Test Post Update",
                content="Test Content Update",
            )
            response = await client.patch(
                f"/api/news/post/{post_id}",
                json=data,
            )
            assert response.status_code == 403
