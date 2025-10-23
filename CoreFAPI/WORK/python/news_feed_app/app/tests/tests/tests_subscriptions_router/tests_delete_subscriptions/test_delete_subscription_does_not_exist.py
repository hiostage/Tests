from typing import TYPE_CHECKING

import pytest
from dependencies.user import get_user
from tests.utils.fake_depends import fake_depends_async, override_dependency
from tests.utils.fake_users import fake_news_maker_user, fake_news_maker_user_2

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from httpx import AsyncClient


@pytest.mark.subscriptions_router
@pytest.mark.asyncio
async def test_delete_subscription_does_not_exist(
    client: "AsyncClient", app: "CustomFastApi"
) -> None:
    """
    Тестирует попытку удаления несуществующей подписки. Ожидается 404 ошибка.

    Шаги:
    1. Использует автора и пользователя (фикстуры fake_news_maker_user, fake_news_maker_user_2).
    2. Пытается отписаться от автора, на которого пользователь не подписан.
    3. Проверяет, что сервер возвращает статус 404 (Not Found).

    :param client: Асинхронный HTTP клиент для выполнения запросов.
    :param app: Экземпляр FastAPI приложения с переопределёнными зависимостями.
    """
    author = fake_news_maker_user
    user = fake_news_maker_user_2

    # Отпишемся от автора на которого мы не подписаны. Ожидаем 404.
    fake_depends_list = [(get_user, fake_depends_async(user))]
    async with override_dependency(app, fake_depends_list):
        response = await client.delete(
            "/api/news/subscription", params={"author_id": str(author.id)}
        )
        assert response.status_code == 404
