from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_author_or_admin_valid_data(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует успешное обновление поста автором или администратором.

    Параметризованные сценарии:
    1. Автор обновляет свой пост
    2. Администратор обновляет чужой пост

    Шаги теста:
    1. Создание тестового поста
    2. Авторизация пользователя (автор/админ)
    3. Отправка PATCH-запроса с новыми данными
    4. Проверка успешного ответа (200 OK)
    5. Верификация обновленных данных в БД

    :param client: Тестовый клиент FastAPI
    :param app: Экземпляр приложения
    :param session: Сессия БД
    """
    user_create_post = fake_news_maker_user
    users_update_post = [fake_news_maker_user, fake_admin_user]

    # Создадим user_create_post простой пост
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id

    for i, user_update_post in enumerate(users_update_post):
        # Забудем всё.
        session.expunge_all()
        # Переопределяем зависимость FastAPI (на user_update_post)
        fake_depends_list = [(get_user, fake_depends_async(user_update_post))]
        # Обновим пост.
        async with override_dependency(app, fake_depends_list):
            data = dict(
                title=f"Test Post Update {i}",
                content=f"Test Content Update {i}",
            )
            response = await client.patch(
                f"/api/news/post/{post_id}",
                json=data,
            )
            assert response.status_code == 200

        # Достанем пост из БД.
        post_in_bd = await session.get(Posts, post_id)
        assert post_in_bd
        # Проверим данные.
        assert post_in_bd.title == data["title"]
        assert post_in_bd.content == data["content"]
