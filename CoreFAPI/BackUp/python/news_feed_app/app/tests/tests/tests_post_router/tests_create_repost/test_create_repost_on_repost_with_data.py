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
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_repost_on_repost_with_data(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание репоста на существующие репосты с контентом или вложениями.

    Проверяет:
    1. Репост репоста с контентом (repost_1):
       - Новый репост должен ссылаться непосредственно на repost_1
    2. Репост репоста с вложениями (repost_2):
       - Новый репост должен ссылаться непосредственно на repost_2
    3. Корректность сохранения связи original_post_id в БД

    :param client: Асинхронный HTTP-клиент для тестирования эндпоинтов
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями
    :param session: Сессия базы данных для проверки сохранённых данных
    """
    user = fake_news_maker_user
    # Создадим пост, на который будем делать репост
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    # Создадим вложение для тестирования
    attachment = Attachments(user_id=user.id, attachment_path="/path/file")

    # Создадим репосты, на который будем делать репост
    # По задумке, если у репоста есть контент или вложения,
    # то у последнего репоста оригинальный пост будет предыдущий репост
    repost_1 = Posts(user_id=uuid.uuid4(), content="content")
    repost_1.original_post = post
    repost_2 = Posts(user_id=uuid.uuid4())
    repost_2.attachments.append(attachment)
    repost_2.original_post = post

    session.add_all([post, repost_1, repost_2])
    await session.commit()
    assert post.id
    assert repost_1.id
    assert repost_2.id
    assert attachment.id

    # Выполним запрос на создание репоста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        for repost in (repost_1, repost_2):
            response = await client.post(f"/api/news/post/{repost.id}/repost", json={})
            assert response.status_code == 200
            response_data = response.json()
            repost_on_repost_id = response_data["post"]["id"]
            assert repost_on_repost_id

            repost_on_repost = await session.get(Posts, repost_on_repost_id)
            assert repost_on_repost
            assert repost_on_repost.original_post_id == repost.id
