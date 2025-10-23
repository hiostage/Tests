import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from sqlalchemy import inspect

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_get_posts_no_lazy_comments(session: "AsyncSession") -> None:
    """
    Тестирует загрузку постов с комментариями и их подсчёт в SQLAlchemy.

    Шаги теста:
        1. Создаёт пост с 2 комментариями в БД.
        2. Сбрасывает кэш сессии (expunge_all).
        3. Повторно загружает пост из БД.
        4. Проверяет состояние ленивой загрузки и счётчик комментариев.

    Проверки:
        - Пост корректно сохраняется и извлекается.
        - Комментарии не загружаются автоматически (unloaded).
        - Comments_count соответствует количеству комментариев.

    :param session: Асинхронная сессия SQLAlchemy (AsyncSession)
    """
    # Создаём новость с 2 комментариями.
    news = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    comments = [
        Comments(user_id=uuid.uuid4(), comment=f"comment {i}") for i in range(2)
    ]
    news.comments.extend(comments)
    session.add(news)
    await session.commit()
    assert news.id
    news_id = news.id
    assert all(bool(comment.id) for comment in comments)

    # Забудем всё
    session.expunge_all()

    # Получаем новость из БД.
    news_1 = await session.get(Posts, news_id)
    assert news_1

    # Проверяем, что наши комментарии НЕ подгрузились из БД.
    insp = inspect(news_1)
    assert "comments" in insp.unloaded

    # Есть данные о количестве
    assert news_1.comments_count == len(comments)
