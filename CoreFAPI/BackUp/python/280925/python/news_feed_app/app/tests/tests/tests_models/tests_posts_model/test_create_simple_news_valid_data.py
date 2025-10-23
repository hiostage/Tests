import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_simple_news_valid_data(session: "AsyncSession") -> None:
    """
    Тест проверяет успешное создание новости с корректными данными.

    Ожидаемое поведение:
    - Новость успешно создаётся и сохраняется в базе данных.

    :param session: Асинхронная сессия для работы с базой данных.
    :return: None.
    """
    news = Posts(
        user_id=uuid.uuid4(),
        title="".join(choices(ascii_letters, k=MAX_TITLE_LENGTH)),
        content="".join(choices(ascii_letters, k=MAX_CONTENT_LENGTH)),
    )
    session.add(news)
    await session.commit()
    assert news.id
