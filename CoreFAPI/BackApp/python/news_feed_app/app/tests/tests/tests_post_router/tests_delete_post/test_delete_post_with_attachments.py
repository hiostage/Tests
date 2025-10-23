from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_delete_post_with_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление поста с вложениями.

    Шаги теста:
    1. Создание поста с вложениями.
    2. Авторизация администратора для удаления поста.
    3. Удаление поста.
    4. Проверка успешного ответа (200 OK).
    5. Верификация отсутствия поста в базе данных.
    6. Проверка, что вложения помечены как удаленные.

    :param client: Тестовый клиент FastAPI
    :param app: Экземпляр приложения FastAPI
    :param session: Асинхронная сессия базы данных
    """
    user = fake_admin_user

    #  Создадим пост с вложениями
    count_attachments = 3
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"path/to/file_{i}")
        for i in range(count_attachments)
    ]
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    post.attachments.extend(attachments)
    session.add(post)
    await session.commit()
    assert post.id
    assert all(bool(att.id) for att in attachments)
    attachments_ids = [att.id for att in attachments]
    post_id = post.id

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Удалим пост.
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{post_id}")
        assert response.status_code == 200

    # Забудем пост.
    session.expunge(post)
    # Забудем вложения
    for att in attachments:
        session.expunge(att)

    # Достанем пост из БД.
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd is None

    # Проверяем, что вложения помечены как удалённые
    attachments_in_bd_q = await session.execute(
        select(Attachments).where(Attachments.id.in_(attachments_ids))
    )
    attachments_in_bd = attachments_in_bd_q.scalars().all()
    assert all(att.is_deleted for att in attachments_in_bd)
