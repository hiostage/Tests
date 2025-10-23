import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from database.models.comments import MAX_COMMENT_LENGTH
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_comments_no_valid_data_comment_db_protection(
    session: "AsyncSession",
) -> None:
    """
    Тестирует защиту БД от создания некорректных комментариев через SQLAlchemy.

    Шаги теста:
        1. Создаёт пост в базе данных.
        2. Пытается добавить комментарий с длиной > MAX_COMMENT_LENGTH.
        3. Проверяет срабатывание защиты БД.

    Проверки:
        - SQLAlchemyError при попытке вставить невалидные данные.
        - Система не позволяет сохранить комментарий с нарушением ограничений.

    :param session: Асинхронная сессия БД (AsyncSession)
    """
    # Создадим простую новость
    news = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    session.add(news)
    await session.commit()
    assert news.id
    news_id = news.id

    # Попробуем создать комментарий
    with pytest.raises(SQLAlchemyError):
        await session.execute(
            insert(Comments).values(
                user_id=uuid.uuid4(),
                post_id=news_id,
                comment="".join(choices(ascii_letters, k=MAX_COMMENT_LENGTH + 1)),
            )
        )
