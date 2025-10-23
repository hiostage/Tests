from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import fake_admin_user
from tests.utils.requests import client_delete_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.media_router
@pytest.mark.asyncio
async def test_delete_file_valid_data_with_relation_to_post(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление вложения, связанного с постом.

    Шаги теста:
    1. Создание поста с прикрепленным вложением
    2. Удаление вложения через API
    3. Проверка, что:
       - Вложение отвязалось от поста
       - Вложение помечено как удаленное

    :param client: Тестовый клиент FastAPI
    :param app: Экземпляр приложения FastAPI
    :param session: Асинхронная сессия базы данных
    """
    user = fake_admin_user
    # Создадим пост с вложением
    attachment = Attachments(user_id=user.id, attachment_path="path/to/attachment")
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    post.attachments.append(attachment)
    session.add(post)
    await session.commit()
    assert post.id
    assert attachment.id
    assert attachment.post_id
    attachment_id = attachment.id
    post_id = post.id
    # Забудем всё
    session.expunge(post)
    session.expunge(attachment)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Удалим вложение.
    response = await client_delete_media(app, fake_depends_list, client, attachment_id)
    assert response.status_code == 200

    # Достанем пост из БД
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd
    # Проверим, что вложение потеряло связь с постом
    assert not post_in_bd.attachments
    attachment_in_bd = await session.get(Attachments, attachment_id)
    assert attachment_in_bd
    assert not attachment_in_bd.post_id
    assert attachment_in_bd.is_deleted
