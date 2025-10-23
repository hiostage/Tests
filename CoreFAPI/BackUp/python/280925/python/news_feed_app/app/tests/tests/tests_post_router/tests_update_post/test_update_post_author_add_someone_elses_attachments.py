import uuid
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
async def test_update_post_author_add_someone_elses_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует невозможность добавления чужих вложений при обновлении поста.

    :param client: AsyncClient для запросов к API
    :param app: Экземпляр FastAPI приложения
    :param session: AsyncSession для взаимодействия с БД

    Шаги теста:
    1. Создаёт пост с вложениями от автора
    2. Добавляет чужое вложение другого пользователя
    3. Пытается обновить пост с чужим вложением
    4. Проверяет, что пост сохранил оригинальные вложения
    """
    user_create_post: "User" = fake_news_maker_user
    count_att = 3
    # Создадим пост с вложениями от пользователя user_create_post
    attachments = [
        Attachments(user_id=user_create_post.id, attachment_path=f"path/to/file_{i}")
        for i in range(count_att)
    ]
    attachments_path = [att.attachment_path for att in attachments]
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    post.attachments.extend(attachments)
    session.add(post)

    # Создадим вложение от другого пользователя
    other_att = Attachments(user_id=uuid.uuid4(), attachment_path="path/to/admin_file")
    session.add(other_att)

    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(att.id) for att in post.attachments)
    assert other_att.id
    att_ids = [att.id for att in post.attachments]

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_create_post))]
    # Обновим пост с чужим вложением.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            attachments_ids=att_ids + [other_att.id],
        )
        response = await client.patch(
            f"/api/news/post/{post_id}",
            json=data,
        )
        assert response.status_code == 200

    # Проверим, что у поста нет чужого вложения
    session.expunge_all()

    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd
    assert set(attachments_path) == set(
        att.attachment_path for att in post_in_bd.attachments
    )
    assert len(post_in_bd.attachments) == count_att
