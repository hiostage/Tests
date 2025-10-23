from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags, PostHashtag
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
async def test_delete_post_with_hashtags(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тест удаления поста с хэштегами.

    :param client: Клиент для отправки запросов
    :param app: Приложение FastAPI
    :param session: Сессия базы данных

    Процесс:
    1. Создаёт пост с 3 хэштегами.
    2. Удаляет пост через API.
    3. Проверяет:
       - Пост удалён из базы данных
       - Связи поста с хэштегами удалены из таблицы PostHashtag
       - Сами хэштеги остались в базе данных
    """
    user = fake_news_maker_user
    # Создадим пост с хэштегами
    hashtags = [Hashtags(name=f"#tag_{i}") for i in range(3)]
    tags_names = [tag.name for tag in hashtags]
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    post.hashtags.extend(hashtags)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(tag.id) for tag in hashtags)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Удалим пост.
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(f"/api/news/post/{post_id}")
        assert response.status_code == 200

    # Забудем всё
    session.expunge_all()

    # Достанем пост из БД.
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd is None

    # Проверим, что связи удалены
    posts_hashtags_q = await session.execute(select(PostHashtag))
    posts_hashtags = posts_hashtags_q.scalars().all()
    assert not posts_hashtags

    # Убедимся, что теги не удалены
    tags_in_bd_q = await session.execute(
        select(Hashtags).where(Hashtags.name.in_(tags_names))
    )
    tags_in_bd = tags_in_bd_q.scalars().all()
    assert tags_in_bd
    assert set(tag.name for tag in tags_in_bd) == set(tags_names)
