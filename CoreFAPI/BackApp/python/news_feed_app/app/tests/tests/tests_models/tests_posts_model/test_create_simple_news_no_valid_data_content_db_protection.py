import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_simple_news_no_valid_data_content_db_protection(
    session: "AsyncSession",
) -> None:
    """
    Тестирование защиты от невалидного содержания новости на уровне базы данных.

    Входные данные:
    - Валидный заголовок длиной MAX_TITLE_LENGTH символов.
    - Содержание длиной MAX_CONTENT_LENGTH + 1 символов.

    Ожидаемый результат:
    - Исключение SQLAlchemyError при попытке сохранить запись в БД.

    :param session: Объект сессии для взаимодействия с базой данных.
    """
    with pytest.raises(SQLAlchemyError):
        await session.execute(
            insert(Posts).values(
                user_id=uuid.uuid4(),
                title="".join(choices(ascii_letters, k=MAX_TITLE_LENGTH)),
                content="".join(choices(ascii_letters, k=MAX_CONTENT_LENGTH + 1)),
            )
        )
