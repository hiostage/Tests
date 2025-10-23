import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags, PostHashtag
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_delete_hashtag_related_to_post(session: "AsyncSession") -> None:
    """
    Тестирует удаление хэштега, связанного с постом.

    :param session: AsyncSession для взаимодействия с БД

    Шаги теста:
    1. Создаёт пост с хэштегом.
    2. Удаляет хэштег из БД.
    3. Проверяет, что хэштег удалён.
    4. Убеждается, что пост остался.
    5. Проверяет, что связь между постом и хэштегом удалена.
    """
    # Создадим пост с хэштегом
    tag = Hashtags(name="#test_tag")

    post = Posts(user_id=uuid.uuid4(), title="title", content="content", hashtags=[tag])
    session.add(post)
    await session.commit()
    assert post.id
    assert tag.id
    tag_id = tag.id
    post_id = post.id

    # Удалим хэштег
    await session.delete(tag)
    await session.commit()

    # Забудем всё
    session.expunge_all()

    # Убедимся, что хэштег удалён
    tag_in_bd = await session.get(Hashtags, tag_id)
    assert tag_in_bd is None

    # Убедимся, что пост не удалён
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd

    # Убедимся, что связь удалена
    posts_hashtags_q = await session.execute(select(PostHashtag))
    posts_hashtags = posts_hashtags_q.scalars().all()
    assert not posts_hashtags
