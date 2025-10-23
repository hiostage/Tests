import pytest_asyncio

from app.db.session import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.schemas.user import UserFull

import app.models

from httpx import AsyncClient, ASGITransport

from app.utils.auth import get_current_user

import uuid
from asgi_lifespan import LifespanManager

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

from app.models.base import Base

engine_test = create_async_engine(TEST_DB_URL, future=True, echo=False)

async_session_maker = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

TEST_UUID = uuid.uuid4()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db():
    async with async_session_maker() as session:
        yield session

async def override_get_current_user():
    return UserFull(
        uuid=str(TEST_UUID),
        firstName="UWU",
        lastName="EZI",
        userName="Uwuwer220",
        phone="+77777777",
        email="Ezstyjsj@mail.ru",
    )

class DammyCache():
    async def delete(self, key):
        return True


from app.main import app
@pytest_asyncio.fixture(scope="function")
async def client():
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    app.dependency_overrides.clear()