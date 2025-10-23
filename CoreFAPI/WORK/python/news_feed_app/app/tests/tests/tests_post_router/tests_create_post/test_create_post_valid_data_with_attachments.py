from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH
from dependencies.user import get_user
from schemas.posts import MAX_ATTACHMENTS
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "user_create_post",
    [fake_news_maker_user, fake_admin_user],
)
@pytest.mark.post_router
@pytest.mark.asyncio
async def test_create_post_valid_data_with_attachments(
    client: "AsyncClient",
    app: "CustomFastApi",
    user_create_post: "User",
    session: "AsyncSession",
) -> None:
    """
    Тестирует создание поста с валидными данными с вложениями.

    Шаги теста:
    1. Создание вложений в БД для тестового пользователя.
    2. Проверка успешного добавления вложений.
    3. Переопределение зависимости FastAPI для авторизации пользователя.
    4. Отправка POST-запроса на создание поста с вложениями.
    5. Проверка успешного ответа API и получения ID созданного поста.
    6. Удаление вложений из сессии для корректной проверки.
    7. Извлечение созданного поста из БД и проверка его данных.

    :param client: Тестовый клиент FastAPI
    :param app: Экземпляр приложения FastAPI
    :param user_create_post: Пользователь, создающий пост (параметризованный)
    :param session: Сессия БД для выполнения операций
    """
    #  Создадим вложения
    attachments = [
        Attachments(user_id=user_create_post.id, attachment_path=f"path/to/file_{i}")
        for i in range(MAX_ATTACHMENTS)
    ]
    attachments_path = [att.attachment_path for att in attachments]
    session.add_all(attachments)
    await session.commit()
    assert all(bool(att.id) for att in attachments)

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user_create_post))]
    # Создадим пост.
    async with override_dependency(app, fake_depends_list):
        data = dict(
            title="".join(choices(ascii_letters, k=MAX_TITLE_LENGTH)),
            content="".join(choices(ascii_letters, k=MAX_CONTENT_LENGTH)),
            attachments_ids=[att.id for att in attachments],
        )
        response = await client.post(
            "/api/news/post",
            json=data,
        )
        assert response.status_code == 200

        post_id = response.json()["post"]["id"]

    # Уберём из сессии attachments
    for att in attachments:
        session.expunge(att)

    # Достаём из БД пост.
    post = await session.get(Posts, post_id)
    assert post
    assert post.title == data["title"]
    assert post.content == data["content"]
    assert set(p_att.attachment_path for p_att in post.attachments) == set(
        attachments_path
    )
