import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Likes, Posts

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_likes_count(session: "AsyncSession") -> None:
    """
    Проверка подсчета лайков у новости.

    :param session: Асинхронная сессия SQLAlchemy
    :return: None

    Тест:
    1. Создает новость с 2 лайками
    2. Проверяет сохранение в БД
    3. Перезагружает и проверяет счетчик
    """
    # Создаём новость с 2 лайками.
    news = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    likes = [Likes(user_id=uuid.uuid4()), Likes(user_id=uuid.uuid4())]
    news.likes.extend(likes)
    session.add(news)
    await session.commit()
    assert news.id

    # Отсоединяем Новость от сессии.
    session.expunge(news)

    # Получаем новость из БД.
    news_1 = await session.get(Posts, news.id)
    assert news_1
    # Проверяем количество лайков.
    assert news_1.likes_count == 2
