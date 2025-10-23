from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from schemas.posts import MAX_ATTACHMENTS
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_exceeding_maximum_number_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание поста с превышением максимального количества вложений.

    Шаги теста:
    1. Создает MAX_ATTACHMENTS + 1 вложений для тестового пользователя.
    2. Проверяет успешное добавление всех вложений в базу данных.
    3. Переопределяет зависимость FastAPI для авторизации пользователя.
    4. Отправляет POST-запрос на создание поста с превышением максимального количества вложений.
    5. Проверяет статус ответа (422 Unprocessable Entity).
    6. Убеждается, что в базе данных нет созданной записи поста.

    :param client: Тестовый клиент FastAPI.
    :param app: Экземпляр приложения FastAPI.
    :param session: Сессия базы данных для выполнения операций.
    """
    user = fake_admin_user
    #  Создадим n+1 вложений от нашего пользователя, где n - это максимальное количество
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"path/to/file_{i}")
        for i in range(MAX_ATTACHMENTS + 1)
    ]
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
        assert response.status_code == 422

    # Убедимся, что в БД нет созданной записи
    posts_q = await session.execute(select(Posts))
    posts = posts_q.scalars().all()
    assert len(posts) == 0
