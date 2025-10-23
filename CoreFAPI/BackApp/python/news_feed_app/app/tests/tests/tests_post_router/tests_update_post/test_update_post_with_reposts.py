import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_with_reposts(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует запрет обновления поста, на который существуют репосты.

    Шаги теста:
    1. Создание оригинального поста и репоста
    2. Попытка обновления заголовка оригинала через API
    3. Проверка блокировки операции

    Проверки:
    - Статус ответа 400 (Bad Request)
    - Система предотвращает изменение поста с существующими репостами

    :param client: Асинхронный HTTP-клиент
    :param app: FastAPI приложение с зависимостями
    :param session: Сессия БД для создания тестовых данных
    """
    user = fake_news_maker_user
    # Создадим пост и репост
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    repost = Posts(user_id=uuid.uuid4(), title="Repost", content="Repost Content")
    repost.original_post = post
    session.add(repost)
    await session.commit()
    assert post.id
    assert repost.id

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Попробуем что-нибудь обновить, ожидаем ошибку, так как нельзя обновлять пост, на который уже сделали репост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="Test Post Update",
        )
        response = await client.patch(
            f"/api/news/post/{post.id}",
            json=data,
        )
        assert response.status_code == 400
