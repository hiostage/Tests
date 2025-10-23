import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Likes, Posts
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_delete_post_with_likes(session: "AsyncSession") -> None:
    """
    Тестирует каскадное удаление лайков при удалении поста.

    Шаги теста:
    1. Создание поста с двумя лайками.
    2. Проверка привязки лайков к посту.
    3. Удаление поста.
    4. Проверка отсутствия поста в базе данных.
    5. Убедиться, что все лайки также удалены.

    :param session: Асинхронная сессия SQLAlchemy.
    """
    # Создадим пост с лайками
    likes = [
        Likes(user_id=uuid.uuid4()),
        Likes(user_id=uuid.uuid4()),
    ]
    post = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    post.likes.extend(likes)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    # Проверим, что лайки привязались к посту
    assert all(bool(like.post_id) for like in post.likes)

    # Удалим пост
    await session.delete(post)
    await session.commit()

    # Проверим, что пост удален
    deleted_post = await session.get(Posts, post_id)
    assert deleted_post is None

    # Проверим, что лайки тоже удалены
    likes_q = await session.execute(select(Likes))
    likes_in_bd = likes_q.scalars().all()
    assert not likes_in_bd
