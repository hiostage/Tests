from typing import TYPE_CHECKING

import pytest
from database.models import Comments
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_create_comment__no_post(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Проверяет создание комментария к несуществующему посту.

    Тест выполняет следующие шаги:
    1. Создает фиктивного авторизованного пользователя
    2. Отправляет POST-запрос к несуществующему посту (post_id=100)
    3. Проверяет, что сервер возвращает статус 404 (Not Found)
    4. Убеждается, что в базе данных не появилось новых комментариев

    :param client: Асинхронный тестовый клиент FastAPI
    :param app: Тестируемое приложение с переопределенными зависимостями
    :param session: Сессия базы данных для проверки результатов
    """
    user = fake_news_maker_user
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            comment="comment",
        )
        response = await client.post(
            "/api/news/post/100/comment",
            json=data,
        )
        assert response.status_code == 404

    # Проверим, что у пользователя нет комментариев
    comments_q = await session.execute(
        select(Comments).where(Comments.user_id == user.id)
    )
    comments = comments_q.scalars().all()
    assert not comments
