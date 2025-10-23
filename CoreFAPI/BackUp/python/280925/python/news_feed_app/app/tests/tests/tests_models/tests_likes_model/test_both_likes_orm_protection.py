import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Likes, Posts

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_both_likes_orm_protection(session: "AsyncSession") -> None:
    """
    Тестирует защиту ORM от одновременного лайка поста и комментария.

    Шаги теста:
    1. Создаёт пост с комментарием
    2. Пытается создать лайк с привязкой одновременно к посту и комментарию
    3. Проверяет срабатывание валидаторов модели

    Проверки:
    - ORM вызывает ValueError при нарушении бизнес-правила
    - Срабатывание валидатора comment_id при наличии post_id
    - Защита от невалидных состояний на уровне модели

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
    with pytest.raises(ValueError):
        like = Likes(user_id=uuid.uuid4())
        like.post = post
        like.comment = comment
        session.add(like)
        await session.commit()
