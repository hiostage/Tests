import uuid
from random import choices
from string import ascii_letters

import pytest
from database.models import Posts
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_simple_news_no_valid_data_title_orm_protection() -> None:
    """
    Тест проверяет попытку создания новости с заголовком, который превышает заданные ограничения.

    Ожидаемое поведение:
    - Возникает исключение ValueError, так как длина заголовка новости превышает допустимые пределы.
    - Валидация данных происходит до сохранения в БД.

    :return: None.
    """

    with pytest.raises(ValueError):
        Posts(
            user_id=uuid.uuid4(),
            title="".join(choices(ascii_letters, k=MAX_TITLE_LENGTH + 1)),
            content="".join(choices(ascii_letters, k=MAX_CONTENT_LENGTH)),
        )
