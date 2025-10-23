import uuid
from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_anonymous_user

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_get_subscription_no_auth_user(
    client: "AsyncClient", app: "CustomFastApi"
) -> None:
    """
    Тестирует попытку получения информации о подписке анонимным (неавторизованным) пользователем.
    Ожидается ошибка 403 Forbidden.

    Шаги:
    1. Использует анонимного пользователя (фикстура fake_anonymous_user).
    2. Выполняет GET-запрос на проверку подписки с произвольным UUID автора.
    3. Проверяет, что сервер возвращает статус 403.

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    user = fake_anonymous_user

    # Попробуем обратится к роуту анонимным пользователем. Ожидаем 403.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.get(
            "/api/news/subscription", params={"author_id": str(uuid.uuid4())}
        )
        assert response.status_code == 403
