import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_post_with_attachments(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует получение поста с вложениями через API.

    Шаги теста:
        1. Создаётся пост с несколькими вложениями в базе данных.
        2. Выполняется GET-запрос к API для получения поста по его ID.
        3. Проверяется статус ответа и содержимое вложений.

    Проверки:
        - Статус ответа 200.
        - Количество вложений в ответе соответствует количеству созданных вложений.
        - Идентификаторы, пути и подписи вложений в ответе соответствуют созданным данным.

    :param client: HTTP клиент для тестирования API.
    :param session: Асинхронная сессия базы данных.
    :param app: Инстанс FastAPI.
    """
    # Создадим пост с вложениями
    users = [fake_auth_user, fake_anonymous_user]
    count_attachments = 3
    attachments = [
        Attachments(
            user_id=uuid.uuid4(),
            attachment_path=f"path/to/file_{i}",
            caption=f"caption_{i}",
        )
        for i in range(count_attachments)
    ]
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    post.attachments.extend(attachments)
    session.add(post)
    await session.commit()
    assert post.id
    assert all(bool(att.id) for att in attachments)

    for user in users:
        # Выполним запрос
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            response = await client.get(f"/api/news/post/{post.id}")
            assert response.status_code == 200

    # Проверим полученные данные последнего.
    data = response.json()
    assert data["post"]["attachments"]
    attachments_response = data["post"]["attachments"]
    assert len(attachments_response) == count_attachments
    assert set(att["id"] for att in attachments_response) == set(
        att.id for att in attachments
    )
    assert set(att["url"] for att in attachments_response) == set(
        att.attachment_path for att in attachments
    )
    assert set(att["caption"] for att in attachments_response) == set(
        att.caption for att in attachments
    )
