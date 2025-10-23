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
async def test_create_repost_valid_data(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание репоста с валидными данными и пустым телом запроса.

    Проверяет:
    1. Создание репоста с полным набором данных:
       - Заголовок
       - Контент
       - Хештеги
       - Вложения
    2. Создание репоста с пустым телом запроса
    3. Корректность ответа API:
       - Статус код 200
       - Наличие ID репоста в ответе
    4. Корректность сохранения в БД:
       - Связь репоста с оригинальным постом (original_post_id)

    :param client: Асинхронный HTTP-клиент для тестирования эндпоинтов
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями
    :param session: Сессия базы данных для проверки сохранённых данных
    """
    user = fake_news_maker_user
    # Создадим пост, на который будем делать репост
    post = Posts(user_id=uuid.uuid4(), title="title", content="content")
    session.add(post)
    # Создадим вложения для репоста
    attachments = [
        Attachments(user_id=user.id, attachment_path=f"/path/{i}") for i in range(3)
    ]
    session.add_all(attachments)
    await session.commit()
    attachments_ids = [att.id for att in attachments]
    assert post.id
    assert all(attachments_ids)

    data_1 = {
        "title": "title repost",
        "content": "content repost",
        "hashtag_names": ["#hashtag1", "#hashtag2"],
        "attachments_ids": attachments_ids,
    }

    # Попробуем создать репост с полным набором данных и полностью пустым
    fake_depends_list = [(get_user, fake_depends_async(user))]

    async with override_dependency(app, fake_depends_list):
        for data in [data_1, {}]:
            response = await client.post(f"/api/news/post/{post.id}/repost", json=data)
            assert response.status_code == 200
            response_data = response.json()
            repost_id = response_data["post"]["id"]
            assert repost_id

            repost = await session.get(Posts, repost_id)
            assert repost
            assert repost.original_post_id == post.id
            if data:
                assert set(att.id for att in repost.attachments) == set(attachments_ids)
                assert set(tag.name for tag in repost.hashtags) == set(
                    data["hashtag_names"]
                )
                assert repost.content == data["content"]
                assert repost.title == data["title"]
            else:
                assert repost.content is None
                assert repost.title is None
                assert not repost.hashtags
                assert not repost.attachments
            session.expunge_all()
