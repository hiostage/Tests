from typing import TYPE_CHECKING

import pytest
from database.models.hashtags import MAX_HASHTAG_LENGTH, Hashtags

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "tag",
    [
        " #good ",  # Пробелы вокруг хэштега
        "#good",  # Стандартный хэштег
        "#g",  # Короткий хэштег
        "#good_tag",  # Хэштег с подчеркиванием
        "#123",  # Хэштег с цифрами
        "#a1b2c",  # Хэштег с буквами и цифрами
        "#Always_Lower",  # Хэштег с большими буквами (будет приведено к нижнему регистру)
        "#{}".format("g" * (MAX_HASHTAG_LENGTH - 1)),  # Хэштег максимальной длины
        "#привет",  # Русский хэштег
        "#你好",  # Китайский хэштег
    ],
)
@pytest.mark.models
@pytest.mark.asyncio
async def test_hashtag_valid_data(session: "AsyncSession", tag: str) -> None:
    """
    Тест: Создание валидных хэштегов.

    Проверяет, что хэштеги с валидным форматом успешно сохраняются в базе данных.

    :param session: Сессия базы данных для выполнения теста.
    :param tag: Входной хэштег для проверки.
    """
    hashtag = Hashtags(name=tag)
    session.add(hashtag)
    await session.commit()
    assert hashtag.id
    assert hashtag.name == hashtag.name.strip().lower()
