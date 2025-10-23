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
async def test_delete_post_with_hashtags(session: "AsyncSession") -> None:
    """
    Тестирует удаление поста с хэштегами.

    :param session: AsyncSession для взаимодействия с БД

    Шаги теста:
    1. Создаёт пост с несколькими хэштегами.
    2. Удаляет пост из БД.
    3. Проверяет, что пост удалён.
    4. Убеждается, что хэштеги остались.
    5. Проверяет, что связь между постом и хэштегами удалена.
    """
    # Создадим пост с тегами
    tags_names = ["#test_tag_1", "#test_tag_2"]
    tags = [Hashtags(name=tag_name) for tag_name in tags_names]
    post = Posts(user_id=uuid.uuid4(), title="title", content="content", hashtags=tags)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(tag.id) for tag in tags)

    # Удалим пост
    await session.delete(post)
    await session.commit()

    # Забудем всё
    session.expunge_all()

    # Убедимся, что пост удалён
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd is None

    # Убедимся, что теги не удалены
    tags_in_bd_q = await session.execute(
        select(Hashtags).where(Hashtags.name.in_(tags_names))
    )
    tags_in_bd = tags_in_bd_q.scalars().all()
    assert tags_in_bd
    assert set(tag.name for tag in tags_in_bd) == set(tags_names)

    # Убедимся, что связь удалена
    posts_hashtags_q = await session.execute(select(PostHashtag))
    posts_hashtags = posts_hashtags_q.scalars().all()
    assert not posts_hashtags
