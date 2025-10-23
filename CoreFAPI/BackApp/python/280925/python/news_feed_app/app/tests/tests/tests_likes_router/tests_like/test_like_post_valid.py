from typing import TYPE_CHECKING

import pytest
from database.models import Likes
from dependencies.user import get_user
from sqlalchemy import select
from tests.tests.tests_likes_router.utils import get_valid_post
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.likes_router
@pytest.mark.asyncio
async def test_like_post_valid(client: "AsyncClient", app: "CustomFastApi") -> None:
    """
    Проверяем лайк на пост.
    Ситуация: Пытаемся поставить лайк на пост.
    Ожидаем ответ 200.

    :param client: AsyncClient.
    :param app: CustomFastApi.
    :return: None.
    """

    fake_depends_list = [(get_user, fake_depends_async(fake_auth_user))]

    async with override_dependency(app, fake_depends_list):

        session_maker = app.get_db().get_session_fabric()
        async with session_maker() as session:
            valid_post = await get_valid_post(session)

            response = await client.post(f"/api/news/post/{valid_post.id}/like")
            assert response.status_code == 200
            assert response.json()["result"]

            like_in_bd_q = await session.execute(
                select(Likes).where(
                    Likes.user_id == fake_auth_user.id, Likes.post_id == valid_post.id
                )
            )
            like_in_bd = like_in_bd_q.scalars().one_or_none()
            assert like_in_bd
