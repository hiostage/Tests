import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from schemas.posts import MAX_ATTACHMENTS
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_repost_exceeding_maximum_number_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание репоста с превышением максимального допустимого количества вложений.

    Проверяет:
    1. Попытку создания репоста с количеством вложений, превышающим MAX_ATTACHMENTS
    2. Корректность возвращаемой ошибки валидации (422 Unprocessable Entity)

    :param client: Асинхронный HTTP-клиент для тестирования эндпоинтов
    :param app: Экземпляр FastAPI приложения
    :param session: Сессия базы данных для создания тестовых данных
    """
    user = fake_news_maker_user
    # Создадим пост, на который будем делать репост
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    # Создадим вложения для репоста (количество превышает допустимое значение)
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"/path/{i}")
        for i in range(MAX_ATTACHMENTS + 1)
    ]
    session.add_all([post, *attachments])
    await session.commit()
    assert post.id
    assert all(bool(att.id) for att in attachments)

    attachments_ids = [att.id for att in attachments]
    data = {
        "attachments_ids": attachments_ids,
    }
    # Попробуем создать репост с вложениями, число которых превышает допустимое значение,
    # ожидаем ошибку
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/post/{post.id}/repost", json=data)
        assert response.status_code == 422
