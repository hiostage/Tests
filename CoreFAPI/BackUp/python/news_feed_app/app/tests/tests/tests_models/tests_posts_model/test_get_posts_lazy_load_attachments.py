import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Attachments, Posts

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.models
@pytest.mark.asyncio
async def test_get_news_lazy_attachments(session: "AsyncSession") -> None:
    """
    Тест проверяет, что при получении новости из базы данных связанные вложения
    загружаются сразу с использованием стратегии 'selectin'.

    Ожидаемое поведение:
    - Новость успешно загружается из базы данных.
    - Связанные вложения загружаются сразу.

    :param session: Асинхронная сессия для работы с базой данных.
    :return: None.
    """
    # Создаём новость с двумя вложениями.
    user_id = uuid.uuid4()
    attachments = [
        Attachments(user_id=user_id, attachment_path="path_1"),
        Attachments(user_id=user_id, attachment_path="path_2"),
    ]
    news = Posts(
        user_id=uuid.uuid4(),
        title="title",
        content="content",
    )
    news.attachments.extend(attachments)
    session.add(news)
    await session.commit()
    assert news.id
    assert attachments[0].id
    assert attachments[1].id

    # Отсоединяем Новость от сессии.
    session.expunge(news)

    # Получаем новость из БД.
    news_1 = await session.get(Posts, news.id)
    assert news_1

    # Проверяем, что наши вложения автоматически подгрузились из БД.
    assert news_1.attachments
    assert all(bool(att.id) for att in news_1.attachments)
    assert all(bool(att.attachment_path) for att in news_1.attachments)
