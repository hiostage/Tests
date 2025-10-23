import os
from dotenv import load_dotenv

env_file = os.getenv("ENV_FILE", ".env.test")
load_dotenv(dotenv_path=env_file)

from fastapi import FastAPI
import pytest, pytest_asyncio
from httpx import AsyncClient, ASGITransport, Response
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
from app.utils.rabbitmq import RabbitMQManager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from app.models.user import User
from app.schemas.group import GroupWithMembers
from app.schemas.user import UserCache, UserPublic
from app.models.group import Group
from datetime import datetime

from app.models import Post
from app.schemas.post import PostWithAuthor, PostCreate, PostUpdate

from unittest.mock import AsyncMock, patch
import json

os.environ["TESTING"] = "1"

@pytest.fixture(autouse=True)
def init_cache():
    FastAPICache.init(InMemoryBackend())

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def rabbit_connection():
    connection = await RabbitMQManager.get_connection()
    yield connection
    await connection.close()

# Тестовая БД (сессионная область)
@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@test_db:5432/test_db",
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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

# Очистка БД (автоматическая после каждого теста)
@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session, rabbit_connection):  # явно зависим от rabbit_connection
    yield
    await db_session.execute(delete(User))
    await db_session.commit()
    await rabbit_connection.close()  # явное закрытие соединения

@pytest_asyncio.fixture
async def auth_client_for_real_sess(client):
    # Просто устанавливаем cookie, которая сработает с MOCK_USERS
    client.cookies.set("sessionId", "test_session")
    return client
#MOCK SESSION#
############################################################
MOCK_USERS = {
    "test_session": {
        "uuid": "d4fbe5146e",
        "firstName": "VLsAD",
        "lastName": "GAsB",
        "userName": "VGaberskorn",
        "email": "v.gaberskorn@mail.ru",
        "phone": None,
        "roles": None,
        "is_active": True,
    },
    "another_session": {
        "uuid": "d407b8f468",
        "firstName": "VLAD",
        "lastName": "GAB",
        "userName": "VGberskorn",
        "email": "v.gabrskorn@mail.ru",
        "phone": None,
        "roles": None,
        "is_active": True,
    },
}

def make_fake_response(user_data: dict) -> Response:
    return Response(
        status_code=200,
        content=json.dumps(user_data),
        headers={"Content-Type": "application/json"}
    )

@pytest_asyncio.fixture
async def auth_client(client):
    client.cookies.set("sessionId", "test_session")
    with patch("app.utils.auth.httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = make_fake_response(MOCK_USERS["test_session"])
        yield client

@pytest_asyncio.fixture
async def readonly_client(client):
    client.cookies.set("sessionId", "another_session")
    with patch("app.utils.auth.httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = make_fake_response(MOCK_USERS["another_session"])
        yield client

####################################################



@pytest_asyncio.fixture
def mock_user():
    return {
        "uuid": "d4fbe514e5",
        "userName": "testuser",
        "firstName": "VLsAD",
        "lastName": "GAsB",
        "email": "testuser@test.com",
        "is_active": True,
        "permissions": ["groups.write"]
    }



@pytest_asyncio.fixture
def mock_auth_service(httpx_mock):
    if os.getenv("USE_HTTPX_MOCK", "true") == "true":
        # Мокаем auth-service
        httpx_mock.add_response(
            url="http://auth-service/api/v1/users/1",
            method="GET",
            json={"uuid": 'fbe514e', "userName": "test_user"},
        )

        # Мокаем другие сервисы
        httpx_mock.add_response(
            url="http://external-service/api/data",
            method="POST",
            json={"data": "mocked"},
        )


@pytest.fixture
def mock_creator():
    return User(
        id="d4fbe514e5",
        username="creator",
        email="creator@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow(),
        first_name= "VLsAD",
        last_name= "GAsB",
    )


@pytest.fixture
def user_factory():
    return User(
        id="d4fbe514",
        username="member",
        email="member@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow(),
        first_name= "VLssAD",
        last_name= "GAsdB",
    )


@pytest.fixture
def mock_group(mock_creator):
    return Group(
        id=1,
        name="Old Name",
        category="technology",
        description=None,
        is_public=True,
        creator_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        slug="old-name",
        banner_url=None,
        rules=None,
        tags=[],
        member_count=1,
        creator=mock_creator
    )


@pytest.fixture
def group_with_members_factory():
    def _factory(
        group_id=1,
        name="Updated",
        creator=None,
        members=None,
        description=None
    ):
        if not creator:
            creator = User(
                id="d4fbe514e5",
                username="creator",
                email="creator@example.com",
                is_active=True,
                last_sync_at=datetime.utcnow()
            )
        if members is None:
            members = [creator]

        return GroupWithMembers(
            id=group_id,
            name=name,
            category="technology",
            description=description,
            is_public=True,
            creator_id=creator.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            slug=name.lower(),
            banner_url=None,
            rules=None,
            tags=[],
            member_count=len(members),
            creator=UserPublic.from_orm(creator),
            members=[UserPublic.from_orm(m) for m in members],
            is_member=True
        )
    return _factory


#POSTS#


@pytest.fixture
def mock_post(mock_group, mock_creator):
    return Post(
        id=1,
        group_id=mock_group.id,
        title="Test Post",
        content="This is a test post.",
        author_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

@pytest.fixture
def post_data(mock_group):
    return {
        "group_id": mock_group.id,
        "title": "Test Post",
        "content": "This is a test post."
    }


@pytest.fixture
def post_with_author_factory(mock_creator):
    def _factory(
        post_id=1,
        group_id=1,
        title="Test Post",
        content="This is a test post.",
        author_id=None,
        created_at=None,
        updated_at=None
    ):
        now = datetime.utcnow()
        return PostWithAuthor(
            id=post_id,
            group_id=group_id,
            title=title,
            content=content,
            author_id=author_id or mock_creator.id,
            created_at=created_at or now,
            updated_at=updated_at or now,
            author=UserPublic.from_orm(mock_creator)
        )
    return _factory
