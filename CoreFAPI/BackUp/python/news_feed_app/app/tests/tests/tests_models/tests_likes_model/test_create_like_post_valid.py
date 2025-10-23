import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Likes, Posts

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_like_post_valid(session: "AsyncSession") -> None:
    """
    Ставим валидный лайк на пост.

    :param session: Сессия БД.
    :return: None.
    """
    valid_post = Posts(
        user_id=uuid.uuid4(),
        title="".join("test_post_1"),
        content="".join("test_content_1"),
    )
    session.add(valid_post)
    await session.flush()

    valid_like = Likes(user_id=uuid.uuid4(), post_id=valid_post.id)
    session.add(valid_like)
    await session.flush()

    assert valid_like.id
