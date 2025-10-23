import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from database.models.comments import MAX_COMMENT_LENGTH

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_comments_no_valid_data_comment_orm_protection(
    session: "AsyncSession",
) -> None:
    """
    Тестирует ORM-валидацию длины комментария при создании объекта.

    Шаги теста:
        1. Создаёт пост в базе данных.
        2. Пытается создать объект комментария с превышением MAX_COMMENT_LENGTH.
        3. Проверяет срабатывание встроенной валидации.

    Проверки:
        - ValueError при попытке создания невалидного комментария.
        - Защита на уровне ORM (декоратор @validates).

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

    with pytest.raises(ValueError):
        Comments(
            user_id=uuid.uuid4(),
            post_id=news_id,
            comment="".join(choices(ascii_letters, k=MAX_COMMENT_LENGTH + 1)),
        )
