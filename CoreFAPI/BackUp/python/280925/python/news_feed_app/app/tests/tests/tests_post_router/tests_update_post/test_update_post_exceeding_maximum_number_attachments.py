from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from schemas.posts import MAX_ATTACHMENTS
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_exceeding_maximum_number_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует попытку обновления поста с превышением максимального количества вложений.

    Шаги теста:
    1. Создает пост с максимальным количеством вложений.
    2. Добавляет дополнительное вложение в базу данных.
    3. Переопределяет зависимость FastAPI для авторизации пользователя.
    4. Отправляет PATCH-запрос на обновление поста с указанием дополнительного вложения.
    5. Проверяет статус ответа.
    6. Убеждается, что данные поста в базе остались неизменными.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user = fake_news_maker_user
    # Создадим пост с максимальным количеством вложений
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"path/to/file_{i}")
        for i in range(MAX_ATTACHMENTS)
    ]
    attachments_path = set(att.attachment_path for att in attachments)
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    post.attachments.extend(attachments)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(att.id) for att in post.attachments)
    att_ids = [att.id for att in post.attachments]

    # Создадим дополнительное вложение
    plus_attachment = Attachments(user_id=user.id, attachment_path="path/to/file")
    session.add(plus_attachment)
    await session.commit()
    assert plus_attachment.id

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Обновим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="Test Post Update",
            content="Test Content Update",
            attachments_ids=att_ids + [plus_attachment.id],
        )
        response = await client.patch(
            f"/api/news/post/{post_id}",
            json=data,
        )
        assert response.status_code // 100 == 4

    # Забудем пост.
    session.expunge(post)
    # Достанем пост из БД.
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd
    # Проверим данные.
    assert post_in_bd.title != data["title"]
    assert post_in_bd.content != data["content"]
    assert (
        set(att.attachment_path for att in post_in_bd.attachments) == attachments_path
    )
