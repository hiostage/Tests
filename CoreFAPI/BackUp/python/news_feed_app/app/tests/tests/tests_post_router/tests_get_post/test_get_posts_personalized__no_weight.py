import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from httpx import QueryParams
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_get_posts_personalized__no_weight(
    client: "AsyncClient",
    session: "AsyncSession",
    app: "CustomFastApi",
) -> None:
    """
    Тестирует пагинацию в персонализированной ленте при отсутствии данных для персонализации.

    Сценарий:
    - Создаём 21 пост от разных авторов
    - Проверяем для двух типов пользователей (авторизованный и анонимный):
      * При запросе 3 страницы с лимитом 10 получаем 1 пост
      * Общее количество страниц равно 3
      * Персонализация не применяется (посты возвращаются по дате создания)

    :param client: Асинхронный HTTP клиент для тестов API
    :param session: Асинхронная сессия базы данных
    :param app: Тестовое приложение FastAPI с зависимостями
    """

    # Создадим 21 пост, ожидаем 3 страницы и на последней 1 пост,
    # т.к. пользователь ничего не лайкал, то и персонализации не будет (недостаточно данных)
    users = [fake_news_maker_user, fake_anonymous_user]
    count_posts = 21
    posts = [
        Posts(
            user_id=uuid.uuid4(),
            title=f"post {i} user",
            content=f"content {i} user",
        )
        for i in range(count_posts)
    ]
    session.add_all(posts)
    await session.commit()
    assert all(bool(post.id) for post in posts)

    for user in users:
        # Получим посты через персонализацию, ожидаем на 3 странице 1 пост
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            param = QueryParams({"page": 3, "limit": 10})
            response = await client.get("/api/news/posts/personalized", params=param)
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) == 1
        assert data["count_pages"] == 3
