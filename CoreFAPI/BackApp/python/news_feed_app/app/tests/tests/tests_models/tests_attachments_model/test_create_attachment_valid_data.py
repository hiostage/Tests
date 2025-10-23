import uuid
from random import choices
from string import ascii_letters
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments
from database.models.attachments import MAX_CAPTION_LENGTH

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "caption",
    [None, "".join(choices(ascii_letters, k=MAX_CAPTION_LENGTH))],
)
@pytest.mark.models
@pytest.mark.asyncio
async def test_create_attachment_valid_data(
    session: "AsyncSession", caption: str | None
) -> None:
    """
    Тестирование создания вложения с валидными данными.

    Проверяет, что вложение успешно сохраняется в базе данных с различными вариантами описания
    (пустое или максимально длинное).

    :param session: Асинхронная сессия базы данных.
    :param caption: Описание вложения (None или строка максимальной длины).
    """
    attachment = Attachments(
        user_id=uuid.uuid4(), attachment_path="path/to/file", caption=caption
    )
    session.add(attachment)
    await session.commit()
    assert attachment.id
