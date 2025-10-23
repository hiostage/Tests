import asyncio
from typing import TYPE_CHECKING

import pytest
from app_utils.start_func import run_consumer
from database.models import AuthorWeight, Likes, Posts
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_dislike_post_update_weight_author(
    client: "AsyncClient", app: "CustomFastApi", session: "AsyncSession"
) -> None:
    """
    Тестирует обновление веса автора при удалении лайка с поста.

    Шаги теста:
    - Создаёт пост с лайком пользователя.
    - Выполняет запрос на удаление лайка.
    - Проверяет, что запрос выполнен успешно (HTTP 200).
    - Проверяет, что вес автора для пользователя после удаления лайка стал равен 0.

    :param client: Асинхронный HTTP клиент для тестирования API.
    :param app: Экземпляр тестового приложения FastAPI с переопределёнными зависимостями.
    :param session: Асинхронная сессия базы данных.
    :return: None
    """
    run_consumer(app)
    author = fake_news_maker_user
    user = fake_news_maker_user_2
    # Создадим пост в БД с лайком (вес автора будет создан автоматически)
    post = Posts(user_id=author.id, title="title", content="content")
    like = Likes(user_id=user.id)
    post.likes.append(like)
    session.add(post)
    await session.commit()
    assert post.id
    assert like.id

    # Уберём лайк с поста
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{like.post_id}/like")
        assert response.status_code == 200

    await asyncio.sleep(2)
    # Проверим, что после дизлайка вес автора для пользователя стал равен 0
    weight_author_for_current_user_q = await session.execute(
        select(AuthorWeight).where(
            AuthorWeight.user_id == user.id, AuthorWeight.author_id == author.id
        )
    )
    weight_author_for_current_user = (
        weight_author_for_current_user_q.scalars().one_or_none()
    )
    assert weight_author_for_current_user
    assert weight_author_for_current_user.weight == 0
