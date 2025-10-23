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
async def test_update_post_only_attachment_2(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тест обновления поста, заменяя вложение на новое.

    :param client: Клиент для отправки запросов
    :param app: Приложение FastAPI
    :param session: Сессия базы данных

    Процесс:
    1. Создаёт пост с одним вложением.
    2. Создаёт новое вложение для замены.
    3. Подменяет зависимости для получения фейкового пользователя.
    4. Обновляет вложения поста, заменяя старое на новое.
    5. Проверяет статус ответа (должен быть 200 OK).
    6. Получает обновлённый пост из базы данных.
    7. Проверяет, что вложение было заменено на новое.
    8. Проверяет, что старое вложение было помечено как удалённое.
    """
    user_create_post: "User" = fake_news_maker_user

    # Создадим пост с вложением
    old_path = "path/to/file"
    old_att = Attachments(user_id=user_create_post.id, attachment_path=old_path)
    post = Posts(user_id=user_create_post.id, title="Test Post", content="Test Content")
    post.attachments.append(old_att)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert old_att.id
    old_att_id = old_att.id

    # Создадим новое вложение, для будущей подмены
    new_path = "path/to/new_file"
    new_att = Attachments(user_id=user_create_post.id, attachment_path=new_path)
    session.add(new_att)
    await session.commit()
    assert new_att.id

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_create_post))]
    # Обновим attachments у поста, заменив старое на новое.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            attachments_ids=[new_att.id],
        )
        response = await client.patch(
            f"/api/news/post/{post_id}",
            json=data,
        )
        assert response.status_code == 200

    # Забудем всё
    session.expunge_all()

    # Достанем пост из БД
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd
    assert post_in_bd.attachments
    assert len(post_in_bd.attachments) == 1
    new_att_in_bd: Attachments = post_in_bd.attachments[0]
    assert new_att_in_bd.attachment_path == new_path

    # Проверим, что старое вложение помечено, как удалённое
    old_att_in_bd = await session.get(Attachments, old_att_id)
    assert old_att_in_bd
    assert old_att_in_bd.is_deleted
