import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Likes, Posts
from sqlalchemy import inspect

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_get_news_no_lazy_likes(session: "AsyncSession") -> None:
    """
    Тест проверяет, что при загрузке новости из базы данных связанные лайки
    не загружаются автоматически (ленивая загрузка).

    :param session: Асинхронная сессия SQLAlchemy для работы с БД.

    Шаги теста:
        1. Создаётся новость с двумя лайками.
        2. Новость и лайки сохраняются в базе.
        3. Сессия очищается, чтобы сбросить кэш.
        4. Новость загружается заново из базы.
        5. Проверяется, что связанные лайки не загружены (ленивая загрузка).

    Ожидаемый результат:
        - Связь "likes" не загружена автоматически после запроса новости.
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
    news_id = news.id

    # Забудем всё
    session.expunge_all()

    # Получаем новость из БД.
    news_1 = await session.get(Posts, news_id)
    assert news_1

    # Проверяем, что наши лайки НЕ подгрузились из БД.
    insp = inspect(news_1)
    assert "likes" in insp.unloaded
