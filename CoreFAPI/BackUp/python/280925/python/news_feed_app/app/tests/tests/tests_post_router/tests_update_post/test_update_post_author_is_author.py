from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_author_is_author(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует обновление поста администратором, при этом автор поста остается неизменным.

    Шаги теста:
    1. Создание поста автором.
    2. Авторизация администратора для обновления поста.
    3. Отправка PATCH-запроса с новыми данными.
    4. Проверка успешного ответа (200 OK).
    5. Автор остался прежним.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user_create_post: "User" = fake_news_maker_user
    user_update_post: "User" = fake_admin_user

    # Создадим user_create_post простой пост
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id

    # Переопределяем зависимость FastAPI (на user_update_post)
    fake_depends_list = [(get_user, fake_depends_async(user_update_post))]
    # Обновим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="Test Post Update",
            content="Test Content Update",
        )
        response = await client.patch(
            f"/api/news/post/{post_id}",
            json=data,
        )
        assert response.status_code == 200

    # Забудем пост.
    session.expunge(post)
    # Достанем пост из БД.
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd
    # Проверим что автор остался прежним
    assert post_in_bd.user_id == user_create_post.id
