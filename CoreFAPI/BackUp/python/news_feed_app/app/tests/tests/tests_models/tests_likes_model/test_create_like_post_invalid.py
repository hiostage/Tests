import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Likes, Posts
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_like_post_invalid(session: "AsyncSession") -> None:
    """
    Пытаемся сохранить 2 одинаковых лайка.
    Должны получить IntegrityError при создании 2-го лайка.

    :param session: Сессия БД.
    :return: None.
    """
    user_1 = uuid.uuid4()
    valid_post = Posts(
        user_id=uuid.uuid4(),
        title="".join("test_post_1"),
        content="".join("test_content_1"),
    )
    session.add(valid_post)
    await session.flush()

    valid_like = Likes(user_id=user_1, post_id=valid_post.id)
    session.add(valid_like)
    await session.flush()

    with pytest.raises(IntegrityError):
        invalid_like = Likes(user_id=user_1, post_id=valid_post.id)
        session.add(invalid_like)
        await session.flush()
