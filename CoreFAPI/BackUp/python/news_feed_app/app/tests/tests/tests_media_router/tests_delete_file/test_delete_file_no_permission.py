from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async
from tests.utils.fake_users import (
    fake_anonymous_user,
    fake_auth_user,
)
from tests.utils.requests import client_delete_media

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient
    from schemas.users import User


@pytest.mark.parametrize("user", [fake_auth_user, fake_anonymous_user])
@pytest.mark.media_router
@pytest.mark.asyncio
async def test_delete_file_no_permission(
    client: "AsyncClient", app: "CustomFastApi", user: "User"
) -> None:
    """
    Тестирует запрет удаления файла без прав доступа через API.

    Шаги теста:
        1. Пользователь пытается удалить файл.
        2. Выполняется DELETE-запрос к API.
        3. Проверяется статус ответа.

    Проверки:
        - Статус ответа 403 (доступ запрещён).

    :param client: HTTP клиент для запросов (AsyncClient).
    :param app: Инстанс FastAPI с зависимостями.
    :param user: Тестовый пользователь (авторизованный/аноним).
    """

    # Не создаём ничего, так как ожидаем 403 (Forbidden)
    # Переопределяем зависимость FastAPI
    fake_depends_list = [(get_user, fake_depends_async(user))]
    # Пробуем удалить изображение.
    response = await client_delete_media(app, fake_depends_list, client, 100)
    assert response.status_code == 403
