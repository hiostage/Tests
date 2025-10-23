# tests/conftest.py
import pytest
from app.utils.auth import AuthenticatedUser

@pytest.fixture
def mock_auth_user():
    return AuthenticatedUser(
        id=1,
        username="test_user",
        is_active=True
    )

@pytest.fixture
def mock_auth(monkeypatch, mock_auth_user):
    async def mock_get_user(*args, **kwargs):
        return mock_auth_user
    
    monkeypatch.setattr("app.utils.auth.get_current_user", mock_get_user)