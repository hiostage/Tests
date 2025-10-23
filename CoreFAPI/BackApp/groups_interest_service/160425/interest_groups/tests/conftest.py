import os
from dotenv import load_dotenv

env_file = os.getenv("ENV_FILE", ".env.test")
load_dotenv(dotenv_path=env_file)

from fastapi import FastAPI
import pytest, pytest_asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from asgi_lifespan import LifespanManager
from app.main import app
from app.services.user import UserService
from app.models.user import User
from app.models.base import Base
from sqlalchemy import delete
from sqlalchemy.pool import NullPool
from app.db.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import test_settings

os.environ["TESTING"] = "1"

engine = create_async_engine("postgresql+asyncpg://...", echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Тестовая БД (сессионная область)
@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
        poolclass=NullPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

# Фабрика сессий (сессионная область)
@pytest.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


# Создание сессии
@pytest_asyncio.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise

@pytest_asyncio.fixture
async def client():
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

# Очистка БД (автоматическая после каждого теста)
@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session):
    yield
    await db_session.execute(delete(User))
    await db_session.commit()

# Авторизованный клиент (эмулируем сессию от другого сервиса)
@pytest_asyncio.fixture
async def auth_client(client):
    # Просто устанавливаем cookie, которая сработает с MOCK_USERS
    client.cookies.set("session_id", "test_session")
    return client

@pytest_asyncio.fixture
async def readonly_client(client):
    client.cookies.set("session_id", "another_session")
    return client


@pytest_asyncio.fixture
def mock_user():
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "testuser@test.com",
        "is_active": True,
        "permissions": ["groups.write"]
    }

@pytest_asyncio.fixture
def mock_group():
    return {
        "name": "Test Group",
        "category": "Tech"
    }


@pytest_asyncio.fixture
def mock_auth_service(httpx_mock):
    if os.getenv("USE_HTTPX_MOCK", "true") == "true":
        # Мокаем auth-service
        httpx_mock.add_response(
            url="http://auth-service/api/v1/users/1",
            method="GET",
            json={"id": 1, "username": "test_user"},
        )

        # Мокаем другие сервисы
        httpx_mock.add_response(
            url="http://external-service/api/data",
            method="POST",
            json={"data": "mocked"},
        )


