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
async def test_create_repost_on_repost_no_data(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание репоста на репост без контента/вложений.

    Проверяет, что при репосте репоста без собственного контента и вложений:
    1. Новый репост ссылается НЕ на промежуточный репост, а на оригинальный пост
    2. Цепочка репостов автоматически "схлопывается" до исходного контента
    3. Корректно сохраняется связь с оригиналом в БД
    """

    user = fake_news_maker_user
    # Создадим пост, на который будем делать репост
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    # Создадим репост, на который будем делать репост
    repost = Posts(user_id=uuid.uuid4())
    repost.original_post = post

    session.add_all([post, repost])
    await session.commit()
    assert post.id
    assert repost.id

    # По задумке, если у репоста нет контента или вложений,
    # то у последнего репоста оригинальный пост будет первый пост.
    # Выполним запрос на создание репоста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/post/{repost.id}/repost", json={})
        assert response.status_code == 200
        response_data = response.json()
        repost_on_repost_id = response_data["post"]["id"]
        assert repost_on_repost_id
    repost_on_repost = await session.get(Posts, repost_on_repost_id)
    assert repost_on_repost
    assert repost_on_repost.original_post_id == post.id
