import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models.attachments import MAX_CAPTION_LENGTH, Attachments
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_attachment_no_valid_caption_bd_protection(
    session: "AsyncSession",
) -> None:
    """
    Тестирование защиты от невалидного описания вложения на уровне базы данных.

    Входные данные:
    - Описание длиной MAX_CAPTION_LENGTH + 1 символов.

    Ожидаемый результат:
    - Исключение SQLAlchemyError при попытке сохранить запись в БД.

    :param session: Объект сессии для взаимодействия с базой данных.
    """
    caption = "".join(choices(ascii_letters, k=MAX_CAPTION_LENGTH + 1))
    with pytest.raises(SQLAlchemyError):
        await session.execute(
            insert(Attachments).values(
                user_id=uuid.uuid4(), attachment_path="path/to/file", caption=caption
            )
        )
