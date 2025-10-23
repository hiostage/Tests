import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app  # путь до твоего FastAPI-приложения
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.services.user import UserService
import json
from unittest.mock import AsyncMock, patch
from starlette.responses import Response

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client

@pytest.fixture
def override_user_dependency():
    async def mock_user_dependency():
        return "123"  # фейковый user_id
    app.dependency_overrides[UserService.get_user_id_from_session] = mock_user_dependency
    yield
    app.dependency_overrides.pop(UserService.get_user_id_from_session, None)

@pytest_asyncio.fixture
async def client_with_auth(async_client: AsyncClient):
    async_client.cookies.set("sessionId", "d4fbe514-eadc-46e5-808c-e4b707b8f468")  # добавляем cookie напрямую
    yield async_client




MOCK_USERS = {
    "test_session": {
        "uuid": "d4fbe514e5",
        "firstName": "VLsAD",
        "lastName": "GAsB",
        "userName": "VGaberskorn",
        "email": "v.gaberskorn@mail.ru",
        "phone": None,
        "roles": None,
        "is_active": True,
    }
}

def make_fake_response(user_data: dict) -> Response:
    return Response(
        status_code=200,
        content=json.dumps(user_data),
        headers={"Content-Type": "application/json"}
    )

from httpx import ASGITransport
@pytest_asyncio.fixture
async def auth_client_MOCK():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        client.cookies.set("sessionId", "test_session")
        with patch("app.utils.auth.httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = make_fake_response(MOCK_USERS["test_session"])
            yield client