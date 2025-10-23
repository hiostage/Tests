import pytest, pytest_asyncio
from httpx import AsyncClient  # Используем AsyncClient для асинхронных тестов
from fastapi import status
from app.main import app
from unittest.mock import patch, AsyncMock
from app.db.session import get_db
from app.services.group import GroupService
from app.services.user import UserService
from app.models.user import User
from app.schemas.group import GroupWithMembers
from app.schemas.user import UserCache, UserPublic
from app.models.group import Group
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

@pytest.mark.asyncio
async def test_db_connection(engine):
    async with AsyncSession(engine) as session:
        result = await session.execute(select(1))  # Простой запрос для проверки соединения
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_create_group(auth_client: AsyncClient):
    mock_group = Group(
        id=1,
        name="Test Group",
        description="Test description",
        category="technology",
        is_public=True,
        creator_id=1
    )

    mock_user = UserCache(
        id=1,
        username="Test User",
        email="test@example.com",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        permissions=["groups.write"]
    )
    
    with patch("app.services.group.GroupService.create_group", new_callable=AsyncMock) as mock_create, \
         patch("app.services.user.UserService.get_user_by_id", new_callable=AsyncMock) as mock_get_user, \
         patch("app.schemas.group.GroupWithMembers.from_orm") as mock_from_orm:
        
        mock_create.return_value = mock_group
        mock_get_user.return_value = mock_user
        mock_from_orm.return_value = GroupWithMembers(
            id=1,
            name="Test Group",
            description="Test description",
            category="technology",
            slug="test-group",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            creator_id=1,
            is_public=True,
            banner_url=None,
            rules=None,
            tags=[],
            member_count=1,
            creator=UserPublic(
                id=1,
                username="Test User",
                email="test@example.com",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            members=[],
            is_member=True
        )

        response = await auth_client.post(
            "/api/v1/groups/",
            json={
                "name": "Test Group",
                "category": "technology",
                "description": "Test description",
                "is_public": True
            }
        )

        assert response.status_code == 201
        assert response.json()["id"] == 1
        assert response.json()["name"] == "Test Group"

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    response = await client.get("/api/v1/groups/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_groups(auth_client: AsyncClient):
    with patch("app.services.group.GroupService.get_groups", new_callable=AsyncMock) as mock_service:
        mock_service.return_value = {
            "groups": [],
            "total": 0,
            "limit": 100,
            "offset": 0
        }

        response = await auth_client.get("/api/v1/groups/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "groups": [],
            "total": 0,
            "limit": 100,
            "offset": 0
        }


@pytest.mark.asyncio
async def test_add_member_to_group(auth_client: AsyncClient):
    # Подготовка данных
    creator_id = 1
    member_id = 2
    current_user_id = 1

    mock_creator = User(
        id=creator_id,
        username="creator",
        email="creator@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow()
    )

    mock_member = User(
        id=member_id,
        username="member",
        email="member@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow()
    )

    mock_group = Group(
        id=1,
        name="Test Group",
        category="technology",
        description="Some description",
        is_public=True,
        creator_id=creator_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        slug="test-group",
        banner_url=None,
        rules=None,
        tags=[],
        member_count=1,
        creator=mock_creator  # Теперь это ORM-модель, не Pydantic
    )
    # Создаём mock GroupWithMembers
    mock_group_with_members = GroupWithMembers(
        id=1,
        name="Test Group",
        category="technology",
        description="Some description",
        is_public=True,
        creator_id=creator_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        slug="test-group",
        banner_url=None,
        rules=None,
        tags=[],
        member_count=2,
        creator=UserPublic.from_orm(mock_creator),
        members=[UserPublic.from_orm(mock_creator), UserPublic.from_orm(mock_member)],
        is_member=True
    )

    # Настройка моков
    with (
        patch("app.services.user.UserService.sync_user", AsyncMock()),
        patch("app.services.group.GroupService.get_group", AsyncMock(return_value=mock_group)),
        patch("app.services.group.GroupService.add_member_to_group", 
             AsyncMock(return_value=mock_group_with_members)),  # Возвращаем GroupWithMembers
        patch("app.utils.auth.get_current_user", AsyncMock(return_value={"id": current_user_id}))
    ):
        response = await auth_client.post(
            f"/api/v1/groups/{mock_group.id}/members/{member_id}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_group.id
        assert any(m["id"] == member_id for m in data["members"])

@pytest.mark.asyncio
async def test_create_group_with_auth(auth_client):
    response = await auth_client.get("/api/v1/check_auth")
    assert response.status_code == 200
    assert response.json() == {"status": "authenticated", "user_id": 1}

@pytest.mark.asyncio
async def test_update_group(auth_client: AsyncClient):
    # Создаем группу
    group_resp = await auth_client.post(
        "/api/v1/groups/", 
        json={"name": "T2e2s3t", "category": "technology", "is_public": True}
    )
    
    # Проверяем, что создание прошло успешно
    assert group_resp.status_code == status.HTTP_201_CREATED  # Ожидаем 201 статус

    group_data = group_resp.json()

    # Проверяем, что id есть в ответе
    assert "id" in group_data  # Проверяем, что ключ "id" есть в ответе
    group_id = group_data["id"]  # Теперь вы точно получите id

    # Печатаем, чтобы убедиться
    print(group_data)

    # Обновляем группу
    response = await auth_client.put(
        f"/api/v1/groups/{group_id}",
        json={"name": "Updated", "category": "technology"}
    )
    
    # Проверяем статус ответа
    assert response.status_code == status.HTTP_200_OK
    updated_group = response.json()
    
    # Дополнительно проверяем, что данные обновились
    assert updated_group["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_group(auth_client: AsyncClient):
    # Создаем группу
    group_resp = await auth_client.post("/api/v1/groups/", json={"name": "Test", "category": "technology"})
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
        response = await client.post("/api/v1/groups/", json={"name": "Test", "category": "technology"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

