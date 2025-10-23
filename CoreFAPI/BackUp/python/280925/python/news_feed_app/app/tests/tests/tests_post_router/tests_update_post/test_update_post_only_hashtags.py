from typing import TYPE_CHECKING

import pytest
from database.models import Posts
from database.models.hashtags import Hashtags, PostHashtag
from dependencies.user import get_user
from sqlalchemy import select
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.post_router
@pytest.mark.asyncio
async def test_update_post_only_hashtags(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Тест обновления поста, меняя только хэштеги.

    :param client: Клиент для отправки запросов
    :param app: Приложение FastAPI
    :param session: Сессия базы данных

    Процесс:
    1. Создаёт пост с 3 хэштегами.
    2. Создаёт новый хэштег.
    3. Подменяет зависимости для получения фейкового пользователя.
    4. Обновляет хэштеги поста:
       - Удаляет последний хэштег
       - Добавляет существующий новый хэштег и придуманный новый
    5. Проверяет статус ответа (должен быть 200 OK).
    6. Получает обновлённый пост из базы данных.
    7. Проверяет, что хэштеги были обновлены правильно.
    8. Проверяет, что связи между постом и хэштегами обновлены.
    9. Проверяет, что удалённый хэштег остался в базе данных.
    """
    user = fake_news_maker_user

    # Создадим пост с хэштегами
    old_hashtags = [Hashtags(name=f"#tag_{i}") for i in range(3)]
    old_tags_names = [tag.name for tag in old_hashtags]
    post = Posts(user_id=user.id, title="Test Post", content="Test Content")
    post.hashtags.extend(old_hashtags)
    session.add(post)
    await session.commit()
    assert post.id
    post_id = post.id
    assert all(bool(tag.id) for tag in old_hashtags)

    # Создадим ещё один хештег
    new_hashtag = Hashtags(name="#new_tag")
    new_tag_name = new_hashtag.name
    session.add(new_hashtag)
    await session.commit()
    assert new_hashtag.id

    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Уберём последний тег, добавим существующий и добавим к списку только что придуманный.
    new_tag_name_plus = "#new_tag_plus"
    new_list_tags = old_tags_names[:-1] + [new_tag_name, new_tag_name_plus]
    async with override_dependency(app, fake_depends_list):
        data = dict(
            hashtag_names=new_list_tags,
        )
        response = await client.patch(
            f"/api/news/post/{post_id}",
            json=data,
        )
        assert response.status_code == 200

    # Забудем всё
    session.expunge_all()

    # Достанем пост из БД
    post_in_bd = await session.get(Posts, post_id)
    assert post_in_bd

    # Проверим теги, замененный тег не должен быть привязан к посту
    assert set(tag.name for tag in post_in_bd.hashtags) == set(new_list_tags)

    # Проверим связи
    posts_hashtags_q = await session.execute(select(PostHashtag))
    posts_hashtags = posts_hashtags_q.scalars().all()
    assert len(posts_hashtags) == len(new_list_tags)

    # Замененный тег не удалён из бд
    tag_del_in_post = await session.get(Hashtags, old_hashtags[-1].id)
    assert tag_del_in_post
    assert tag_del_in_post.name == old_tags_names[-1]
