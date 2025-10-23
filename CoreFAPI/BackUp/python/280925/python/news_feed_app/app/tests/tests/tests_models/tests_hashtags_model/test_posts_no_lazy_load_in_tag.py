import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags
from sqlalchemy import inspect, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_posts_no_lazy_load_in_tag(session: "AsyncSession") -> None:
    """
    Тест проверяет отсутствие ленивой загрузки постов при получении тега.

    :param session: Асинхронная сессия SQLAlchemy для работы с БД
    :steps:
        1. Создает тег с 2 постами
        2. Сбрасывает кеш сессии (expunge_all)
        3. Загружает тег без подгрузки связанных постов
        4. Проверяет, что связь 'post_hashtags' не загружена
    """
    # Создадим 2 поста с одинаковым тегом
    tag_name = "#test_tag"
    tag = Hashtags(name=tag_name)
    posts = [
        Posts(user_id=uuid.uuid4(), title="title", content="content", hashtags=[tag])
        for _ in range(2)
    ]
    session.add_all(posts)
    await session.commit()
    assert tag.id
    assert all(p.id for p in posts)

    # Забудем всё
    session.expunge_all()

    # Достанем тег из бд
    tag_in_bd_q = await session.execute(
        select(Hashtags).where(Hashtags.name == tag_name)
    )
    tag_in_bd = tag_in_bd_q.scalars().one_or_none()
    assert tag_in_bd

    # Проверяем, что посты НЕ подгрузились
    insp = inspect(tag_in_bd)
    assert "post_hashtags" in insp.unloaded
