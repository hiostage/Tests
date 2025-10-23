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
async def test_create_group(
    auth_client: AsyncClient,
    group_with_members_factory,
    mock_group: Group,
    mock_creator: User
):
    group_with_members = group_with_members_factory(
        group_id=mock_group.id,
        name=mock_group.name,
        creator=mock_creator,
        members=[],  # или какие-то другие пользователи, если нужно
        description=mock_group.description
    )

    with (
        patch("app.services.group.GroupService.create_group", AsyncMock(return_value=mock_group)),
        patch("app.services.user.UserService.get_user_by_id", AsyncMock(return_value=mock_creator)),
        patch("app.schemas.group.GroupWithMembers.from_orm", return_value=group_with_members),
    ):
        response = await auth_client.post(
            "/api/v1/groups/",
            json={
                "name": mock_group.name,
                "category": mock_group.category,
                "description": mock_group.description,
                "is_public": mock_group.is_public
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == mock_group.id
        assert data["name"] == mock_group.name


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
async def test_add_member_to_group(
    auth_client: AsyncClient,
    group_with_members_factory
):
    creator = User(
        id=1,
        username="creator",
        email="creator@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow()
    )
    member = User(
        id=2,
        username="member",
        email="member@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow()
    )

    group = Group(
        id=1,
        name="Test Group",
        category="technology",
        is_public=True,
        creator_id=creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        slug="test-group",
        member_count=1,
        creator=creator
    )

    group_with_members = group_with_members_factory(
        group_id=group.id,
        name="Test Group",
        creator=creator,
        members=[creator, member]
    )

    with (
        patch("app.services.user.UserService.sync_user", AsyncMock()),
        patch("app.services.group.GroupService.get_group", AsyncMock(return_value=group)),
        patch("app.services.group.GroupService.add_member_to_group", AsyncMock(return_value=group_with_members)),
        patch("app.utils.auth.get_current_user", AsyncMock(return_value={"id": creator.id}))
    ):
        response = await auth_client.post(
            f"/api/v1/groups/{group.id}/members/{member.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group.id
        assert any(m["id"] == member.id for m in data["members"])

@pytest.mark.asyncio
async def test_create_group_with_auth(auth_client):
    response = await auth_client.get("/api/v1/check_auth")
    assert response.status_code == 200
    assert response.json() == {"status": "authenticated", "user_id": 1}

@pytest.mark.asyncio
async def test_update_group(
    auth_client: AsyncClient,
    mock_creator: User,
    mock_group: Group,
    group_with_members_factory
):
    # Создаем группу с помощью фабрики
    group_with_members = group_with_members_factory(
        group_id=mock_group.id,
        name=mock_group.name,
        creator=mock_creator,
        members=[],
    )

    # Обновляем mock_group, чтобы он отражал изменения
    updated_group = Group(
        id=mock_group.id,
        name="Updated",  # Обновляем имя группы
        category=mock_group.category,
        description=mock_group.description,
        is_public=mock_group.is_public,
        creator_id=mock_group.creator_id,
        created_at=mock_group.created_at,
        updated_at=datetime.utcnow(),  # Обновляем время
        slug="updated",  # Можно обновить slug, если нужно
        banner_url=mock_group.banner_url,
        rules=mock_group.rules,
        tags=mock_group.tags,
        member_count=mock_group.member_count,
        creator=mock_group.creator,
    )

    # Проверяем, что мок возвращает правильные данные
    with (
        patch("app.services.user.UserService.get_user_by_id", AsyncMock(return_value=mock_creator)),
        patch("app.services.group.GroupService.create_group", AsyncMock(return_value=mock_group)),
        patch("app.services.group.GroupService.update_group", AsyncMock(return_value=updated_group)),  # Мокируем обновление
        patch("app.utils.auth.get_current_user", AsyncMock(return_value={
            "user_id": 1,  # Проверяем, что user_id соответствует создателю
            "is_active": True,
            "permissions": ["groups.write"]
        })),
    ):
        # Создаем группу
        group_resp = await auth_client.post(
            "/api/v1/groups/",
            json={"name": "Old Name", "category": "technology", "is_public": True}
        )

        assert group_resp.status_code == 201
        group_id = group_resp.json()["id"]

        # Обновляем группу, добавляем обязательное поле is_public
        response = await auth_client.put(
            f"/api/v1/groups/{group_id}",
            json={
                "name": "Updated",  # Новое имя
                "category": "technology",
                "is_public": True,
                "banner_url": ""  # Добавляем поле banner_url
            }
        )

        # Логируем весь ответ для диагностики
        print(f"Response JSON: {response.json()}")

        # Проверяем, что возвращаемое значение имеет нужные поля
        updated_group_response = response.json()
        assert "name" in updated_group_response, "Поле 'name' не найдено в ответе"
        assert updated_group_response["name"] == "Updated"
        assert updated_group_response["slug"] == "updated"
        assert updated_group_response["category"] == "technology"
        assert updated_group_response["is_public"] is True

        # Проверяем статус-код ответа
        assert response.status_code == 200


        
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

