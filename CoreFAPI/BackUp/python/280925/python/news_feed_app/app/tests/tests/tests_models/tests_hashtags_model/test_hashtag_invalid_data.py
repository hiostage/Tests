import pytest
from database.models.hashtags import MAX_HASHTAG_LENGTH, Hashtags


@pytest.mark.parametrize(
    "tag",
    [
        "",  # Пустой хэштег
        "#",  # Хэштег без символов после #
        "#good!",  # Хэштег с восклицательным знаком
        "#good@",  # Хэштег со знаком @
        "#good$",  # Хэштег со знаком $
        "#good#bad",  # Хэштег с несколькими символами #
        "#good bad",  # Хэштег с пробелом
        "#{}".format("g" * MAX_HASHTAG_LENGTH),  # Слишком длинный хэштег
    ],
)
@pytest.mark.models
@pytest.mark.asyncio
async def test_hashtag_invalid_data(tag: str) -> None:
    """
    Тест: Создание невалидных хэштегов.

    Проверяет, что попытка создать хэштеги с недопустимыми форматами вызывает ошибку.

    :param tag: Входной хэштег для проверки.
    """

    with pytest.raises(ValueError):
        Hashtags(name=tag)
