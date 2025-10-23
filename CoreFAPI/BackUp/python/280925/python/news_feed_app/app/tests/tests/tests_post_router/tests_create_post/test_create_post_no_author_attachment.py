import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_no_author_attachment(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание поста с вложениями, включая вложение, принадлежащее другому пользователю.

    Шаги теста:
    1. Создает 3 вложения для тестового пользователя и одно вложение от другого пользователя.
    2. Проверяет успешное добавление всех вложений в базу данных.
    3. Переопределяет зависимость FastAPI для авторизации тестового пользователя.
    4. Отправляет POST-запрос на создание поста с указанием всех вложений.
    5. Проверяет успешный статус ответа (200) и получение ID созданного поста.
    6. Извлекает созданный пост из базы данных.
    7. Убедится, что вложение другого пользователя проигнорировано.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user = fake_admin_user
    #  Создадим 3 вложения от нашего пользователя
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"path/to/file_{i}")
        for i in range(3)
    ]
    good_path_set = set(att.attachment_path for att in attachments)
    # И одно от левого пользователя.
    attachments.append(
        Attachments(user_id=uuid.uuid4(), attachment_path="path/to/file")
    )

    session.add_all(attachments)
    await session.commit()
    assert all(bool(att.id) for att in attachments)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Создадим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="Test Post",
            content="Test Content",
            attachments_ids=[att.id for att in attachments],
        )
        response = await client.post(
            "/api/news/post",
            json=data,
        )
        assert response.status_code == 200

        post_id = response.json()["post"]["id"]

    # Уберём из сессии attachments
    for att in attachments:
        session.expunge(att)

    # Достаём из БД пост.
    post = await session.get(Posts, post_id)
    assert post
    assert post.title == data["title"]
    assert post.content == data["content"]
    # Проверяем, что код проигнорировал чужое вложение
    assert set(p_att.attachment_path for p_att in post.attachments) == good_path_set
