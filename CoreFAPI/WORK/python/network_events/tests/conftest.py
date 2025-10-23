import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.schemas.user import UserPublic
from app.utils.auth import get_current_user

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DB_URL, future=True, echo=False)
async_session_maker = sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db():
    async with async_session_maker() as session:
        yield session

async def override_get_current_user():
    return UserPublic(
        uuid="asdkdasd6454d65as",
        firstName="UWU",
        lastName="EZI",
        userName="Uwuwer220",
        phone="+77777777",
        email="Ezstyjsj@mail.ru",
    )

@pytest_asyncio.fixture(autouse=True)
async def clear_db():
    async with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield

@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c 

    app.dependency_overrides.clear()

