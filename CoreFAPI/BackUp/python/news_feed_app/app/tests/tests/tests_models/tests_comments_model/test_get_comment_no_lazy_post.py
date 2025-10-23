import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from sqlalchemy import inspect

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_get_comment_no_lazy_post(session: "AsyncSession") -> None:
    """
    Тестирует отсутствие ленивой загрузки связанного поста при получении комментария.

    Шаги теста:
        1. Создаёт пост с одним комментарием.
        2. Сбрасывает сессию (expunge_all).
        3. Загружает комментарий из базы.
        4. Проверяет, что связанный пост не был загружен автоматически.

    Проверки:
        - Комментарий успешно загружен.
        - Связанный пост находится в состоянии unloaded (ленивая загрузка).

    :param session: Асинхронная сессия SQLAlchemy (AsyncSession)
    """
    # Создаём новость с комментарием.
    news = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    comment = Comments(user_id=uuid.uuid4(), comment="comment")
    news.comments.append(comment)
    session.add(news)
    await session.commit()
    assert news.id
    assert comment.id
    comment_id = comment.id

    # Забудем всё
    session.expunge_all()

    # Достанем коммент из БД
    comment_in_bd = await session.get(Comments, comment_id)
    assert comment_in_bd

    # Проверяем, что пост НЕ подгрузился вместе с комментом
    insp = inspect(comment_in_bd)
    assert "post" in insp.unloaded
