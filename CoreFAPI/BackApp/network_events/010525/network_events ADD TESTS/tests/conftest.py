import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app  # путь до твоего FastAPI-приложения
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.services.user import UserService

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client

@pytest.fixture
def override_user_dependency():
    async def mock_user_dependency():
        return 123  # фейковый user_id
    app.dependency_overrides[UserService.get_user_id_from_session] = mock_user_dependency
    yield
    app.dependency_overrides.pop(UserService.get_user_id_from_session, None)

@pytest_asyncio.fixture
async def client_with_auth(async_client: AsyncClient):
    async_client.cookies.set("session_id", "test_session")  # добавляем cookie напрямую
    yield async_client
