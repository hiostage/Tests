import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_repost_by_id(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует получение репоста по ID через API эндпоинт /api/news/post/{post_id}.

    Создаёт тестовый пост и репост, сохраняет их в базе, затем выполняет GET-запрос
    к эндпоинту для получения репоста и проверяет, что в ответе присутствует
    оригинальный пост.

    :param client: Асинхронный HTTP клиент для выполнения запросов к API.
    :param app: Экземпляр приложения FastAPI с возможностью переопределения зависимостей.
    :param session: Асинхронная сессия базы данных для создания и сохранения тестовых данных.
    :return: None. Тест проверяет корректность ответа и выбрасывает AssertionError при ошибках.
    """
    user = fake_anonymous_user
    # Создадим пост и репост
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    repost = Posts(user_id=uuid.uuid4(), title="Repost", content="Repost Content")
    repost.original_post = post
    session.add(repost)
    await session.commit()
    assert post.id
    assert repost.id

    # Сделаем запрос и убедимся, что оригинальный пост тоже подгрузился
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(f"/api/news/post/{repost.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["post"]["original_post"]
