import pytest
import pytest_asyncio
from httpx import AsyncClient, Request, Response
from app.main import app  # путь до твоего FastAPI-приложения
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fastapi import Depends
from app.services.user import UserService
from app.utils.auth import get_current_user
import json
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db

from app.models.event import Event

from app.db.database import engine, async_session_maker, Base
from sqlalchemy import text

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest_asyncio.fixture
async def client_with_auth(async_client: AsyncClient):
    async_client.cookies.set("sessionId", "d4fbe514-eadc-46e5-808c-e4b707b8f468")  # добавляем cookie напрямую
    yield async_client

MOCK_USERS = {
    "test_session": {
        "uuid": "59af8cb14fb60eaf",
        "firstName": "VxLsAD",
        "lastName": "GAxsB",
        "userName": "VGabexrskorn",
        "email": "v.gabexrskorn@mail.ru",
        "phone": "+7432154234315",
        "password": "$2a$10$wljO/rtdZAXeNm9XbbcFMefEQIsQlvtXwyyVCWbsvkGNQDYNbJgcu",
        "roles": None,
    }
}

event_data = {
    "title": "TEST_EVENT",
    "description": "DISC *NORM*",
    "location": "Ru"
}

def make_fake_response(user_data: dict) -> Response:
    return Response(
        status_code=200,
        content=json.dumps(user_data),
        headers={"Content-Type": "application/json"},
        request=Request("GET", "http://test/user")
    )

@pytest_asyncio.fixture(scope="function", autouse=True)
async def client_get_MOCK():
    real_get = AsyncClient.get  # сохраним оригинал

    async def fake_get(self, url, *args, **kwargs):
        if "user" in str(url):  # или точное условие для авторизационного запроса
            return make_fake_response(MOCK_USERS["test_session"])
        return await real_get(self, url, *args, **kwargs)  # всё остальное по-настоящему

    with patch("app.utils.auth.httpx.AsyncClient.get", new=fake_get):
        yield

@pytest_asyncio.fixture()
async def auth_client_MOCK(client_get_MOCK):
    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        client.cookies.set("sessionId", "test_session")
        yield client







@pytest_asyncio.fixture(scope="function")
async def created_event(auth_client_MOCK: AsyncClient):
    event = await auth_client_MOCK.post("/events/", json=event_data)
    assert event.status_code == 200

    yield event.json()
    event_id = int(event["id"])
    await auth_client_MOCK.delete(f"/event/{event_id}")






@pytest.fixture
def override_user_dependency():
    async def mock_user_dependency():
        return "test_session"  # фейковый user_id
    app.dependency_overrides[get_current_user] = mock_user_dependency
    yield
    app.dependency_overrides.pop(get_current_user, None)

