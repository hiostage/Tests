import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_delete_post_with_repost__author(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует попытку удаления поста с репостами автором исходного поста.

    Создаёт цепочку пост -> репост -> репост репоста, где исходный пост принадлежит пользователю-автору.
    Пытается удалить исходный пост от имени автора, ожидая ошибку 400 Bad Request,
    так как пост нельзя удалить, если на него уже сделали репосты и пользователь не админ.

    После запроса проверяется, что все посты остались в базе данных.

    :param client: Асинхронный HTTP клиент для выполнения запросов к API.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    :param session: Асинхронная сессия базы данных для создания и проверки данных.
    """
    user = fake_news_maker_user
    # Создадим цепочку пост-репост
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    repost_post = Posts(
        user_id=uuid.uuid4(), title="Repost Post", content="Repost Post Content"
    )
    repost_post.original_post = post
    repost_repost = Posts(
        user_id=uuid.uuid4(), title="Repost Repost", content="Repost Repost Content"
    )
    repost_repost.original_post = repost_post
    session.add(repost_repost)
    await session.commit()
    assert repost_repost.id
    assert repost_post.id
    assert post.id
    posts_ids_set = {post.id, repost_post.id, repost_repost.id}

    # Переопределяем зависимость FastAPI (пользователь автор исходного поста)
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Пробуем удалить пост (ожидаем 400)
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{post.id}")
        assert response.status_code == 400

    # Проверим, что всё осталось
    session.expunge_all()

    posts_in_bd_q = await session.execute(select(Posts))
    posts_in_bd = posts_in_bd_q.scalars().all()
    assert posts_in_bd
    assert set(post.id for post in posts_in_bd) == posts_ids_set
