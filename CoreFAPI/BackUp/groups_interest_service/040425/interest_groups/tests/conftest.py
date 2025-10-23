import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
def mock_auth_service(httpx_mock):
    # Мокируем auth service
    httpx_mock.add_response(
        url="http://auth-service/api/v1/users/1",
        json={"id": 1, "username": "test_user"},
        method="GET"
    )
    
    # Мокируем другие сервисы
    httpx_mock.add_response(
        url="http://external-service/api/data",
        json={"data": "mocked"},
        method="POST"
    )