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


@pytest.mark.parametrize(
    "user_create_post, user_delete_post",
    [
        (fake_news_maker_user, fake_news_maker_user),
        (fake_news_maker_user, fake_admin_user),
    ],
)
@pytest.mark.post_router
@pytest.mark.asyncio
async def test_delete_post_author_or_admin(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_post: "User",
    user_delete_post: "User",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление поста автором или администратором.

    Сценарии теста:
    1. Автор удаляет свой пост.
    2. Администратор удаляет пост другого пользователя.

    Шаги теста:
    1. Создание тестового поста.
    2. Авторизация пользователя для удаления поста.
    3. Отправка DELETE-запроса на удаление поста.
    4. Проверка успешного ответа (200 OK).
    5. Убедиться, что пост удален из базы данных.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param user_create_post: Пользователь, создающий пост.
    :param user_delete_post: Пользователь, удаляющий пост.
    :param session: Сессия базы данных для выполнения операций.
    """
    # Создадим user_create_post простой пост
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id

    # Переопределяем зависимость FastAPI (на user_update_post)
    fake_depends_list = [(get_user, fake_depends_async(user_delete_post))]
    # Удалим пост.
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{post_id}")
        assert response.status_code == 200

    # Забудем пост.
    session.expunge(post)
    # Достанем пост из БД.
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd is None
