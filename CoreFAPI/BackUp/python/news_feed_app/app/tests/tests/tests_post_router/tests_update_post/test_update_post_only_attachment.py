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
async def test_update_post_only_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует частичное обновление поста, изменяя только вложения.

    Шаги теста:
    1. Создание поста без вложений.
    2. Добавление вложений в базу данных.
    3. Авторизация пользователя для обновления поста.
    4. Отправка PATCH-запроса с новыми вложениями.
    5. Проверка успешного ответа (200 OK).
    6. Убедиться, что изменились только вложения, а заголовок и содержимое остались неизменными.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user_create_post: "User" = fake_news_maker_user
    # Создадим пост и вложения от пользователя user_create_post
    attachments = [
        Attachments(user_id=user_create_post.id, attachment_path=f"path/to/file_{i}")
        for i in range(3)
    ]
    session.add_all(attachments)
    attachments_path = [att.attachment_path for att in attachments]
    title = "Test Post"
    content = "Test Content"
    post = Posts(user_id=user_create_post.id, title=title, content=content)

    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(att.id) for att in attachments)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_create_post))]
    # Обновим только attachments.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            attachments_ids=[att.id for att in attachments],
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
    # Проверим, что изменился только attachments
    assert post_in_bd.title == title
    assert post_in_bd.content == content
    assert set(att.attachment_path for att in post_in_bd.attachments) == set(
        attachments_path
    )
