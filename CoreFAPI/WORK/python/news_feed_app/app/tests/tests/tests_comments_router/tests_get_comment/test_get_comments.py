import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from httpx import QueryParams
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_get_comments(
    client: "AsyncClient", session: "AsyncSession", app: "CustomFastApi"
) -> None:
    """
    Проверяет корректное получение комментариев с пагинацией.

    Тест создаёт пост с 21 комментарием, затем запрашивает третью страницу с лимитом 10 комментариев.
    Ожидается, что:
    - общее количество страниц равно 3,
    - на третьей странице будет ровно 1 комментарий.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param session: Асинхронная сессия базы данных для подготовки данных.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    """
    user = fake_anonymous_user
    # Создадим пост и 21 комментарий к нему
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    comments = [
        Comments(comment=f"comment_{i}", user_id=uuid.uuid4()) for i in range(21)
    ]
    post.comments.extend(comments)
    session.add(post)
    await session.commit()
    assert post.id
    assert all(bool(comm.id) for comm in comments)

    # Запросим 3-ю страницу, ожидаем увидеть 1 комментарий
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        param = QueryParams({"page": 3, "limit": 10})
        response = await client.get(f"/api/news/post/{post.id}/comments", params=param)
        assert response.status_code == 200
        data = response.json()
        assert data["count_pages"] == 3
        assert len(data["comments"]) == 1
