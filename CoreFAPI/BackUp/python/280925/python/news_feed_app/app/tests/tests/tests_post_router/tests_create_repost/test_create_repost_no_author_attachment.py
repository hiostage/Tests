import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_repost_no_author_attachment(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание репоста с вложениями, среди которых есть вложение, не принадлежащее автору репоста.

    Проверяется, что при создании репоста учитываются только вложения, принадлежащие пользователю,
    который создаёт репост. Вложение другого пользователя игнорируется и не добавляется в репост.

    :param client: Асинхронный HTTP клиент для отправки запросов к API.
    :param app: Экземпляр FastAPI приложения с возможностью переопределения зависимостей.
    :param session: Асинхронная сессия базы данных для создания и проверки тестовых данных.
    """
    user = fake_news_maker_user
    # Создадим пост, на который будем делать репост
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    # Создадим вложения для репоста
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"/path/{i}") for i in range(3)
    ]
    # И одно вложение не от автора репоста.
    attachment_other = Attachments(user_id=uuid.uuid4(), attachment_path="/path/other")

    session.add_all([post, attachment_other, *attachments])
    await session.commit()
    attachments_ids = [att.id for att in attachments]
    assert post.id
    assert all(attachments_ids)
    assert attachment_other.id

    data = {
        "attachments_ids": attachments_ids + [attachment_other.id],
    }

    # Попробуем создать репост с вложениями автора репоста + 1 чужое,
    # ожидаем, что код проигнорирует чужое вложение
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        response = await client.post(f"/api/news/post/{post.id}/repost", json=data)
        assert response.status_code == 200
        response_data = response.json()
        repost_id = response_data["post"]["id"]
        assert repost_id

        repost = await session.get(Posts, repost_id)
        assert repost
        assert repost.original_post_id == post.id

        assert set(att.id for att in repost.attachments) == set(attachments_ids)
