import uuid
from typing import TYPE_CHECKING, Optional

from database.models import Likes, Posts
from tests.utils.checks import has_records_in_bd

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


async def get_valid_post(session: "AsyncSession") -> Posts:
    """
    Cоздаём простой пост для тестирования likes_router.

    :param session: Сессия БД.
    :return: Posts
    """
    valid_post = Posts(
        user_id=uuid.uuid4(),
        title="".join("test_post_1"),
        content="".join("test_content_1"),
    )
    session.add(valid_post)
    await session.commit()
    if not await has_records_in_bd(Posts, session):
        print("Пост пропал. Ищи в недрах кучи")
    return valid_post


async def get_valid_like(user_id: Optional["UUID"], session: "AsyncSession") -> Likes:
    """
    Cоздаём запись в модель Лайков для тестирования likes_router.

    :param user_id: ID текущего пользователя.
    :param session: Сессия БД.
    :return: Likes
    """
    valid_post = await get_valid_post(session)
    valid_like = Likes(user_id=user_id, post_id=valid_post.id)
    session.add(valid_like)
    await session.commit()
    if not await has_records_in_bd(Likes, session):
        print("Пост пропал. Ищи в недрах кучи")
    return valid_like
