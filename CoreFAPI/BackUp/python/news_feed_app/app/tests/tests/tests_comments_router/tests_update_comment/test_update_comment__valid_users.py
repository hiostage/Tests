import uuid
from typing import TYPE_CHECKING

import pytest
from database.models import Comments, Posts
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_admin_user, fake_auth_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.comments_router
@pytest.mark.asyncio
async def test_update_comment__valid_users(
    client: "AsyncClient",
    app: "CustomFastApi",
    session: "AsyncSession",
) -> None:
    """
    Проверяет, что автор комментария и администратор могут успешно обновить текст комментария.

    Тест выполняет следующие шаги:
    1. Создает пост с комментарием, принадлежащим fake_auth_user.
    2. Для каждого пользователя из списка (автор и администратор):
       - Переопределяет зависимость текущего пользователя.
       - Отправляет PATCH-запрос на обновление комментария.
       - Проверяет, что статус ответа 200 OK.
       - Проверяет, что текст комментария в базе данных обновился корректно.

    :param client: Асинхронный HTTP клиент для тестирования FastAPI.
    :param app: Тестируемое FastAPI приложение с переопределёнными зависимостями.
    :param session: Асинхронная сессия базы данных для подготовки и проверки данных.
    """
    users = [fake_auth_user, fake_admin_user]

    # Создадим пост с комментарием
    post = Posts(user_id=uuid.uuid4(), title="Test Post", content="Test Content")
    comment = Comments(user_id=fake_auth_user.id, comment="Test Comment")
    post.comments.append(comment)
    session.add(post)
    await session.commit()
    assert post.id
    assert comment.id
    comment_id = comment.id

    # Пробуем изменить коммент
    for user in users:
        fake_depends_list = [(get_user, fake_depends_async(user))]
        async with override_dependency(app, fake_depends_list):
            new_comment = f"new comment {user.id}"
            data = dict(
                comment=new_comment,
            )
            response = await client.patch(
                f"/api/news/post/comment/{comment_id}",
                json=data,
            )
            assert response.status_code == 200

            # Проверим в БД
            session.expunge_all()
            comment_in_bd = await session.get(Comments, comment_id)
            assert comment_in_bd
            assert comment_in_bd.comment == new_comment
