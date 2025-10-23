from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Generator

import aiofiles
import pytest
import pytest_asyncio
from app_utils.exception_handlers import app_exception_handlers
from app_utils.lifespan import lifespan_func
from core.factory_function import get_app
from database.models.base import Base
from httpx import ASGITransport, AsyncClient
from routers.app_routers import routers
from tests.utils.settings_app import t_settings

if TYPE_CHECKING:
    from app_utils.rabbitmq_manager import RabbitMQClient
    from core.classes.app import CustomFastApi
    from core.classes.settings import Settings
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def settings() -> "Settings":
    """
    Возвращает настройки для тестирования приложения.

    :return: Settings.
    """
    return t_settings


@pytest.fixture
def rabbitmq_client(app: "CustomFastApi") -> Generator["RabbitMQClient", Any, None]:
    """
    Фикстура, принимающая приложение и возвращающая RabbitMQClient.
    После теста очищает очередь.

    :param app: Экземпляр приложения CustomFastApi.
    :return: Генератор, выдающий RabbitMQClient.
    """
    rabbit = app.get_rabbit_client()
    with rabbit.get_connection() as connection:
        channel = connection.channel()
        channel.queue_purge(queue=rabbit.base_routing_key)
        channel.queue_purge(queue=rabbit.inner_routing_key)
    yield rabbit
    with rabbit.get_connection() as connection:
        channel = connection.channel()
        channel.queue_purge(queue=rabbit.base_routing_key)
        channel.queue_purge(queue=rabbit.inner_routing_key)


@pytest_asyncio.fixture
async def app(settings: "Settings") -> AsyncGenerator["CustomFastApi", None]:
    """
    Создаём приложение для тестирования.

    :param settings: Settings.

    :return: AsyncGenerator["CustomFastApi", None].
    """
    test_app = get_app(
        settings=settings,
        lifespan=lifespan_func,
        routers=routers,
        exception_handlers=app_exception_handlers,
    )
    minio_client = test_app.get_minio_client()
    bucket_name = test_app.get_settings().MINIO_SETTINGS.MINIO_BUCKET
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    async with test_app.get_db().get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_app
    async with test_app.get_db().get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    objects = minio_client.list_objects(bucket_name)
    for obj in objects:
        minio_client.remove_object(bucket_name, obj.object_name)


@pytest.fixture
def client(app: "CustomFastApi") -> AsyncClient:
    """
    Фикстура для создания асинхронного тестового клиента.

    :param app: CustomFastApi.
    :return: AsyncClient.
    """
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest_asyncio.fixture
async def image_file() -> bytes:
    """
    Фикстура для реального изображения.

    :return: bytes.
    """
    base_dir = Path(__file__).parent
    image_path = base_dir / "temp" / "image_file.jpg"

    async with aiofiles.open(image_path, "rb") as file:
        image_content = await file.read()

    return image_content


@pytest_asyncio.fixture
async def fake_image_file() -> bytes:
    """
    Фикстура для фейкового изображения.

    :return: bytes.
    """
    base_dir = Path(__file__).parent
    fake_image_path = base_dir / "temp" / "fake_image_file.jpg"

    async with aiofiles.open(fake_image_path, "rb") as file:
        fake_image_content = await file.read()

    return fake_image_content


@pytest_asyncio.fixture
async def session(app: "CustomFastApi") -> AsyncGenerator["AsyncSession", None]:
    """
    Асинхронно создает и предоставляет сессию для работы с базой данных.

    :param app: CustomFastApi.
    :return: AsyncGenerator["AsyncSession", None].
    """
    session_maker = app.get_db().get_session_fabric()
    async with session_maker() as session:
        yield session
