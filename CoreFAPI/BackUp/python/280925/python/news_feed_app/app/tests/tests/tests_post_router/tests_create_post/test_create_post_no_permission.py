from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH, Posts
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize("user", [fake_auth_user, fake_anonymous_user])
@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_no_permission(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
    user: "User",
) -> None:
    """
    Тестирует запрет создания поста пользователем без прав.

    Проверяет сценарий:
    - Пользователь с недостаточными правами пытается создать пост
    - Сервер возвращает 403 Forbidden

    :param client: Тестовый клиент FastAPI
    :param app: Экземпляр приложения
    :param session: Сессия БД
    :param user: Пользователь без прав
    """

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Пробуем создать пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="".join(choices(ascii_letters, k=MAX_TITLE_LENGTH)),
            content="".join(choices(ascii_letters, k=MAX_CONTENT_LENGTH)),
        )
        response = await client.post(
            "/api/news/post",
            json=data,
        )
        assert response.status_code == 403

    # Убедимся, что в БД нет созданной записи
    posts_q = await session.execute(select(Posts))
    posts = posts_q.scalars().all()
    assert len(posts) == 0
