from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_only_content(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует частичное обновление поста, изменяя только его содержимое.

    Шаги теста:
    1. Создание поста с вложениями и заголовком.
    2. Авторизация пользователя для обновления поста.
    3. Отправка PATCH-запроса с новым содержимым.
    4. Проверка успешного ответа (200 OK).
    5. Убедиться, что изменилось только содержимое, а заголовок и вложения остались неизменными.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user_create_post: "User" = fake_news_maker_user
    # Создадим пост с вложениями от пользователя user_create_post
    attachments = [
        Attachments(user_id=user_create_post.id, attachment_path=f"path/to/file_{i}")
        for i in range(3)
    ]
    attachments_path = [att.attachment_path for att in attachments]
    title = "Test Post"
    post = Posts(user_id=user_create_post.id, title=title, content="Test Content")
    post.attachments.extend(attachments)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(att.id) for att in post.attachments)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_create_post))]
    # Обновим только content.
    async with override_dependency(app, fake_depends_list):
        data = dict(
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
    # Проверим, что изменился только content
    assert post_in_bd.title == title
    assert post_in_bd.content == data["content"]
    assert set(att.attachment_path for att in post_in_bd.attachments) == set(
        attachments_path
    )
