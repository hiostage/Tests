import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_delete_post_with_repost__admin(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует удаление поста с репостами пользователем с правами администратора.

    Создаёт цепочку пост -> репост -> репост репоста, сохраняет их в базе.
    Затем с помощью клиента выполняет DELETE-запрос на удаление исходного поста
    от имени администратора. Проверяет, что запрос успешен (статус 200) и что
    после удаления в базе данных не осталось ни одного из связанных постов.

    :param client: Асинхронный HTTP клиент для выполнения запросов к API.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    :param session: Асинхронная сессия базы данных для создания и проверки данных.
    """

    # Создадим цепочку пост-репост
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
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

    # Переопределяем зависимость FastAPI (пользователь админ)
    fake_depends_list = [(get_user, fake_depends_async(fake_admin_user))]
    # Удалим пост.
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{post.id}")
        assert response.status_code == 200

    # Проверим что всё удалено
    session.expunge_all()

    posts_in_bd_q = await session.execute(select(Posts))
    posts_in_bd = posts_in_bd_q.scalars().all()
    assert not posts_in_bd
