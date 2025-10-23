import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_get_posts_lazy_load_tags(session: "AsyncSession") -> None:
    """
    Тестирует ленивую загрузку тегов при получении поста.

    :param session: AsyncSession для взаимодействия с БД

    Шаги теста:
    1. Создаёт пост с тремя тегами.
    2. Фиксирует изменения в БД и проверяет наличие ID.
    3. Сбрасывает кэш сессии.
    4. Получает пост из БД и проверяет, что теги загрузились автоматически.
    """
    # Создадим пост с 3 тегами
    tag_names = [f"#test_tag{i}" for i in range(3)]
    tags = [Hashtags(name=tag_name) for tag_name in tag_names]
    post = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    post.hashtags.extend(tags)
    session.add(post)
    await session.commit()
    assert post.id
    assert all(bool(tag.id) for tag in post.hashtags)
    post_id = post.id

    # Забудем всё
    session.expunge_all()

    # Получим пост из БД
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd
    assert post_in_bd.hashtags

    # Проверим, что теги подгрузились автоматически
    assert set(tag_names) == set(tag.name for tag in post_in_bd.hashtags)
