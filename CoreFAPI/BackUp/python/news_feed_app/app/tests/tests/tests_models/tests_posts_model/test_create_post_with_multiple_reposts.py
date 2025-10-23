import uuid
from typing import TYPE_CHECKING

import pytest
from database.models.posts import Posts

if TYPE_CHECKING:

    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_post_with_multiple_reposts(session: "AsyncSession") -> None:
    """
    Тест проверяет успешное создание новости и 3-х репостов.

    Ожидаемое поведение:
    - Новость и ее репосты успешно создаются и сохраняются в базе данных.

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
    original_id = original.id
    assert all(bool(repost.id) for repost in reposts)
    # Забываем всё
    session.expunge_all()

    original_in_bd = await session.get(Posts, original_id)
    assert original_in_bd
    assert original_in_bd.reposts_count == len(reposts)
