import uuid
from typing import TYPE_CHECKING

import pytest
from database.models.posts import Posts
from sqlalchemy import inspect, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:

    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_create_reposts_chain(session: "AsyncSession") -> None:
    """
    Тестирование цепочки репостов и стратегии загрузки связанных объектов.

    Шаги теста:
    1. Создание оригинального поста
    2. Создание первого репоста (ссылается на оригинал)
    3. Создание второго репоста (ссылается на первый репост)
    4. Проверка загрузки связей:
       - Явная подгрузка original_post для repost2
       - Ленивая загрузка original_post у repost1

    Проверки:
    - Корректность связи repost2 -> repost1
    - Отсутствие неявной загрузки repost1->original_post
    - Сохранение идентификаторов в цепочке

    :param session: Асинхронная сессия SQLAlchemy
    """

    original = Posts(
        user_id=uuid.uuid4(), title="Original Post", content="Original Content"
    )
    session.add(original)
    await session.commit()

    repost1 = Posts(
        user_id=uuid.uuid4(),
        original_post_id=original.id,
        content="Repost Content 1",
    )
    session.add(repost1)
    await session.commit()

    repost1_id = repost1.id

    repost2 = Posts(
        user_id=uuid.uuid4(),
        original_post_id=repost1.id,
        content="Repost Content 2",
    )
    session.add(repost2)
    await session.commit()

    # Забываем всё
    session.expunge_all()

    # Достанем repost2
    stmt = (
        select(Posts)
        .where(Posts.id == repost2.id)
        .options(selectinload(Posts.original_post))
    )
    repost2_in_bd_q = await session.execute(stmt)
    repost2_in_bd = repost2_in_bd_q.scalars().one()

    # Проверим, что оригинальный пост репоста2 подгружен (мы его явно подгрузили)
    assert repost2_in_bd.original_post
    assert repost2_in_bd.original_post.id == repost1_id

    # Проверим, что original_post у репоста1(он же оригинальный пост репоста2) не подгружен
    insp = inspect(repost2_in_bd.original_post)
    assert "original_post" in insp.unloaded
