import pytest, pytest_asyncio
from httpx import AsyncClient  # Используем AsyncClient для асинхронных тестов
from fastapi import status
from app.main import app
from unittest.mock import patch, AsyncMock
from app.db.session import get_db
from app.services.group import GroupService
from app.services.user import UserService

@pytest.mark.asyncio
async def test_create_group(auth_client: AsyncClient):
    with patch("app.services.group.GroupService.create_group", 
              new_callable=AsyncMock) as mock_service:
        mock_service.return_value = {"id": 1, "name": "Test Group"}
        
        response = await auth_client.post(
            "/api/v1/groups/",
            json={"name": "Test Group", "category": "Tech"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/groups/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_groups(auth_client: AsyncClient):
    with patch("app.services.group.GroupService.get_groups",
              new_callable=AsyncMock) as mock_service:
        mock_service.return_value = []
        
        response = await auth_client.get("/api/v1/groups/")
        assert response.status_code == status.HTTP_200_OK

@pytest.fixture
async def admin_client(client):
    # Создаем админа
    admin_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpass",
        "is_admin": True
    }
    await UserService.create_user(admin_data)
    
    # Логинимся
    response = await client.post("/api/v1/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    
    client.cookies.update({"session_id": response.cookies.get("session_id")})
    return client

@pytest.mark.asyncio
async def test_admin_access(admin_client):
    response = await admin_client.get("/api/v1/admin/groups")
    assert response.status_code == status.HTTP_200_OK





@pytest.mark.asyncio
async def test_add_member_to_group(auth_client: AsyncClient):
    # Создаем группу
    group_resp = await auth_client.post("/api/v1/groups/", json={"name": "Test", "category": "Tech"})
    group_id = group_resp.json()["id"]
    
    # Добавляем участника
    response = await auth_client.post(
        f"/api/v1/groups/{group_id}/members/2"  # предполагаем, что пользователь с ID 2 существует
    )
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_update_group(auth_client: AsyncClient):
    # Создаем группу
    group_resp = await auth_client.post("/api/v1/groups/", json={"name": "Test", "category": "Tech"})
    group_id = group_resp.json()["id"]
    
    # Обновляем
    response = await auth_client.put(
        f"/api/v1/groups/{group_id}",
        json={"name": "Updated", "category": "Tech"}
    )
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_group(auth_client: AsyncClient):
    # Создаем группу
    group_resp = await auth_client.post("/api/v1/groups/", json={"name": "Test", "category": "Tech"})
    group_id = group_resp.json()["id"]
    
    # Удаляем
    response = await auth_client.delete(f"/api/v1/groups/{group_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.asyncio
async def test_create_group_no_permissions(client: AsyncClient):
    mock_user_no_perms = {
        "user_id": 1,
        "username": "nopermsuser",
        "email": "noperms@test.com",
        "is_active": True,
        "permissions": []
    }
    
    with patch("app.api.groups.get_current_user", return_value=mock_user_no_perms):
        response = await client.post("/api/v1/groups/", json={"name": "Test", "category": "Tech"})
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_logout(auth_client: AsyncClient):
    # Проверяем доступ
    response = await auth_client.get("/api/v1/groups/")
    assert response.status_code == status.HTTP_200_OK
    
    # Выходим
    await auth_client.post("/api/v1/logout")
    
    # Проверяем снова
    response = await auth_client.get("/api/v1/groups/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED