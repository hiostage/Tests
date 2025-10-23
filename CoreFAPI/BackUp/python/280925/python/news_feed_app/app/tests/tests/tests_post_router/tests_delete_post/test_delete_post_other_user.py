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
async def test_delete_post_other_user(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление поста сторонними пользователями через API.

    Шаги теста:
        1. Создаёт пост от имени основного пользователя.
        2. Последовательно имитирует DELETE-запросы от:
           • Другого создателя
           • Обычного пользователя
           • Анонима
        3. Проверяет доступ к удалению и сохранность поста.

    Проверки:
        - Статус 403 для всех непривилегированных пользователей.
        - Пост остаётся в базе после попыток удаления.

    :param client: Асинхронный HTTP-клиент (AsyncClient)
    :param app: FastAPI приложение с зависимостями
    :param session: Асинхронная сессия БД (AsyncSession)
    """
    user_create_post = fake_news_maker_user
    users_delete_post = [fake_news_maker_user_2, fake_auth_user, fake_anonymous_user]

    # Создадим user_create_post простой пост
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id

    for user in users_delete_post:
        # Забудем всё.
        session.expunge_all()
        # Переопределяем зависимость FastAPI (на user_delete_post)
        fake_depends_list = [(get_user, fake_depends_async(user))]
        # Пробуем удалить пост.
        async with override_dependency(app, fake_depends_list):
            response = await client.delete(f"/api/news/post/{post_id}")
            assert response.status_code == 403

        # Достанем пост из БД.
        post_in_bd = await session.get(Posts, post_id)
        assert post_in_bd
