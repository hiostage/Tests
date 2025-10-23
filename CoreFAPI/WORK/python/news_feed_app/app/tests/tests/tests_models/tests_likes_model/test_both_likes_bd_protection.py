import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Likes, Posts
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_both_likes_bd_protection(session: "AsyncSession") -> None:
    """
    Тестирует защиту на уровне БД при одновременном лайке поста и комментария.

    Шаги теста:
    1. Создаёт пост с комментарием
    2. Пытается создать лайк через прямой SQL-insert с нарушением CheckConstraint
    3. Проверяет срабатывание защиты на уровне БД

    Проверки:
    - БД вызывает SQLAlchemyError при нарушении CheckConstraint
    - Срабатывание ограничения only_one_target
    - Защита от невалидных состояний на уровне схемы БД

    :param session: Асинхронная сессия SQLAlchemy
    """
    # Создадим пост с комментарием
    post = Posts(
        user_id=uuid.uuid4(),
        title="".join("test_post_1"),
        content="".join("test_content_1"),
    )
    comment = Comments(user_id=uuid.uuid4(), comment="comment")
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id

    # Попробуем поставить лайк сразу посту и комментарию, ожидаем ошибку
    with pytest.raises(SQLAlchemyError):
        await session.execute(
            insert(Likes).values(
                user_id=uuid.uuid4(),
                post_id=post.id,
                comment_id=comment.id,
            )
        )
