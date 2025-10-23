import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Likes, Posts

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_comment_likes_count(session: "AsyncSession") -> None:
    """
    Тестирование автоматического подсчёта лайков комментария.

    Шаги:
    1. Создание тестовых данных:
       - Пост с комментарием
       - 3 лайка для комментария
    2. Проверка корректного сохранения в БД
    3. Верификация счётчика лайков

    Проверки:
    - Все сущности успешно сохранены
    - Счётчик лайков соответствует количеству добавленных лайков
    """
    comment_likes_count = 3
    # Создадим пост, комментарий к нему и comment_likes_count лайков к этому комментарию
    post = Posts(user_id=uuid.uuid4(), title="test", content="test")
    comment = Comments(user_id=uuid.uuid4(), comment="test")
    likes = [Likes(user_id=uuid.uuid4()) for _ in range(comment_likes_count)]
    post.comments.append(comment)
    comment.likes.extend(likes)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id
    comment_id = comment.id
    assert all(bool(like.id) for like in likes)

    # Забудем всё
    session.expunge_all()

    # Достанем наш комментарий из БД
    comment_in_bd = await session.get(Comments, comment_id)
    assert comment_in_bd
    # Проверим, что likes_count у комментария отображает верное количество лайков
    assert comment_in_bd.likes_count == comment_likes_count
