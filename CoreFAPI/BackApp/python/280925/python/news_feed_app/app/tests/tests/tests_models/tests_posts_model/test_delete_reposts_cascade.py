import uuid
from typing import TYPE_CHECKING

import pytest
from database.models.posts import Posts
from sqlalchemy import select

if TYPE_CHECKING:

    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_delete_reposts_cascade(session: "AsyncSession") -> None:
    """
    Тест проверяет удаление репостов при удалении оригинального поста.

    :param session: Асинхронная сессия для работы с базой данных.
    :return: None.
    """
    original = Posts(
        user_id=uuid.uuid4(), title="Original Post", content="Original Content"
    )
    reposts = [
        Posts(
            user_id=uuid.uuid4(),
            content=f"Repost Content №{i}",
        )
        for i in range(3)
    ]
    for repost in reposts:
        repost.original_post = original

    session.add_all(reposts)
    await session.commit()
    assert original.id
    assert all(bool(repost.id) for repost in reposts)

    await session.delete(original)
    await session.commit()

    # Забываем всё
    session.expunge_all()

    posts_q = await session.execute(select(Posts))
    posts = posts_q.scalars().all()
    assert not posts
