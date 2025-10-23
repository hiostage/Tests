import uuid
from random import choices
from string import ascii_letters

import pytest
from database.models.attachments import MAX_CAPTION_LENGTH, Attachments


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_attachment_no_valid_caption_orm_protection() -> None:
    """
    Тестирование создания вложения с невалидным описанием.

    Проверяет, что:
    1. При попытке создать объект Attachments с описанием длиннее MAX_CAPTION_LENGTH
       выбрасывается исключение ValueError
    2. Валидация данных происходит до сохранения в БД
    """
    caption = "".join(choices(ascii_letters, k=MAX_CAPTION_LENGTH + 1))
    with pytest.raises(ValueError):
        Attachments(
            user_id=uuid.uuid4(), attachment_path="path/to/file", caption=caption
        )
