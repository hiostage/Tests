from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
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
async def test_update_post_admin_add_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует успешное обновление поста администратором с добавлением новых вложений.

    Сценарий:
    - Автор создает пост с вложениями.
    - Администратор добавляет свои вложения к посту и обновляет его.
    - Проверяется успешный статус ответа (200 OK).
    - Проверяется, что все вложения (автора и администратора) добавлены к посту.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user_create_post: "User" = fake_news_maker_user
    user_update_post: "User" = fake_admin_user
    # Создадим пост с вложениями от пользователя user_create_post
    attachments = [
        Attachments(user_id=user_create_post.id, attachment_path=f"path/to/file_{i}")
        for i in range(3)
    ]
    attachments_path = [att.attachment_path for att in attachments]
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    post.attachments.extend(attachments)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(att.id) for att in post.attachments)
    att_ids = [att.id for att in post.attachments]

    # Создадим вложения от user_update_post (он же админ)
    admin_attachments = [
        Attachments(
            user_id=user_update_post.id, attachment_path=f"path/to/admin_file_{i}"
        )
        for i in range(3)
    ]
    admin_attachments_path = [att.attachment_path for att in admin_attachments]
    session.add_all(admin_attachments)
    await session.commit()
    assert all(bool(att.id) for att in admin_attachments)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_update_post))]
    # Обновим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            attachments_ids=[att.id for att in admin_attachments] + att_ids,
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
    attachments_path.extend(admin_attachments_path)
    assert set(att.attachment_path for att in post_in_bd.attachments) == set(
        attachments_path
    )
