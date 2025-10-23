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

import aio_pika

@pytest.mark.asyncio
async def test_rabbitmq_message_delivery():
    queue_name = "groups.new_post"
    test_message = b"test_message_delivery"

    # Подключение к брокеру
    connection = await aio_pika.connect_robust("amqp://user:password@rabbitmq/")

    async with connection:
        channel = await connection.channel()

        # Убедимся, что очередь существует
        queue = await channel.declare_queue(queue_name, durable=True)

        # Отправка сообщения
        await channel.default_exchange.publish(
            aio_pika.Message(body=test_message),
            routing_key=queue_name,
        )

        # Получение сообщения
        incoming_message = await queue.get(timeout=5)
        await incoming_message.ack()

        assert incoming_message.body == test_message



@pytest.mark.asyncio
async def test_db_connection(engine):
    async with AsyncSession(engine) as session:
        result = await session.execute(select(1))  # Простой запрос для проверки соединения
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_create_group_with_auth(auth_client):
    response = await auth_client.get("/api/v1/groups/check_auth")
    assert response.status_code == 200
    assert response.json() == {"status": "authenticated", "uuid": "d4fbe5146e"}


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
        members=[],  # или другие пользователи, если нужно
        description=mock_group.description
    )

    with (
        patch("app.services.group.GroupService.create_group", AsyncMock(return_value=mock_group)),
        patch("app.services.user.UserService.get_user_by_id", AsyncMock(return_value=mock_creator)),
        patch("app.services.user.UserService.sync_user", AsyncMock()),
        patch("app.schemas.group.GroupWithMembers.from_group", return_value=group_with_members),
        patch("app.utils.rabbitmq.RabbitMQManager.publish_event", AsyncMock())  # Мок для публикации события
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

from app.schemas.user import UserPublic  # Импортируй свою схему

from app.schemas.user import UserPublic  # Импортируй свою схему

@pytest.mark.asyncio
async def test_add_member_to_group(
    auth_client: AsyncClient,
    group_with_members_factory
):
    creator = User(
        id="d4fbe514e5",
        username="creator",
        email="creator@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow(),
        first_name="VLsAD",
        last_name="GAsB",
    )
    member = User(
        id="d4fbe514",
        username="member",
        email="member@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow(),
        first_name="VLssAD",
        last_name="GAsdB",
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

    # 💥 Важно: мокаем get_current_user как UserPublic
    fake_user_public = UserPublic(
        id=creator.id,
        username=creator.username,
        email=creator.email,
        is_active=True,
        created_at=None
    )

    with (
        patch("app.services.user.UserService.sync_user", AsyncMock()),
        patch("app.services.group.GroupService.get_group", AsyncMock(return_value=group)),
        patch("app.services.group.GroupService.add_member_to_group", AsyncMock(return_value=group_with_members)),
        patch("app.utils.rabbitmq.RabbitMQManager.publish_event", AsyncMock()),
        patch("app.utils.auth.get_current_user_for_posts", AsyncMock(return_value=fake_user_public))
    ):
        response = await auth_client.post(
            f"/api/v1/groups/{group.id}/members/{member.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group.id
        assert any(m["id"] == member.id for m in data["members"])



@pytest.mark.asyncio
async def test_remove_member_from_group(
    auth_client: AsyncClient,
    group_with_members_factory
):
    creator = User(
        id='1',
        username="creator",
        email="creator@example.com",
        is_active=True,
        last_sync_at=datetime.utcnow()
    )
    member = User(
        id='2',
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
        member_count=2,
        creator=creator,
        members=[creator, member]
    )

    # После удаления участника
    updated_group = group_with_members_factory(
        group_id=group.id,
        name="Test Group",
        creator=creator,
        members=[creator]  # Только создатель остался
    )

    with (
        patch("app.services.group.GroupService.get_group", AsyncMock(return_value=group)),
        patch("app.services.group.GroupService.remove_member", AsyncMock(return_value=updated_group)),
        patch("app.utils.auth.get_current_user", AsyncMock(return_value={"uuid": creator.id}))
    ):
        response = await auth_client.delete(
            f"/api/v1/groups/{group.id}/members/{member.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group.id
        assert all(m["id"] != member.id for m in data["members"])


@pytest.mark.asyncio
async def test_update_group(auth_client: AsyncClient, mock_creator: User, mock_group: Group):
    # Убедимся, что creator_id совпадает
    mock_group.creator_id = mock_creator.id
    
    updated_group = Group(
        id=mock_group.id,
        name="Updated",
        category=mock_group.category,
        description=mock_group.description,
        is_public=mock_group.is_public,
        creator_id=mock_group.creator_id,
        created_at=mock_group.created_at,
        updated_at=datetime.utcnow(),
        slug="updated",
        banner_url=mock_group.banner_url,
        rules=mock_group.rules,
        tags=mock_group.tags,
        member_count=mock_group.member_count,
        creator=mock_group.creator,
    )

    with (
        patch("app.services.group.GroupService.get_group", 
             AsyncMock(return_value=mock_group)),
        patch("app.services.group.GroupService.update_group", 
             AsyncMock(return_value=updated_group)),
        patch("app.utils.auth.get_current_user", 
             AsyncMock(return_value={
                 "uuid": mock_creator.id,
                 "is_active": True,
                 "permissions": ["groups.write"]
             })),
    ):
        response = await auth_client.put(
            f"/api/v1/groups/{mock_group.id}",
            json={
                "name": "Updated",
                "category": "technology",
                "is_public": True,
                "banner_url": ""
            }
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response JSON: {response.text}")
        assert response.status_code == 200

        
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_delete_group(auth_client: AsyncClient, mock_creator: User):
    mock_group = Group(
        id=1,
        name="Test",
        category="technology",
        is_public=True,
        creator_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        member_count=1,
    )

    with (
        patch("app.services.user.UserService.get_user_by_id", AsyncMock(return_value=mock_creator)),
        patch("app.services.group.GroupService.get_group", AsyncMock(return_value=mock_group)),
        patch("app.services.group.GroupService.delete_group", AsyncMock(return_value=None)),
        patch("app.utils.auth.get_current_user", AsyncMock(return_value={
            "uuid": mock_creator.id,
            "is_active": True,
            "permissions": ["groups.write"]
        })),
    ):
        # DELETE напрямую, минуя POST, так как мы мокаем get_group
        response = await auth_client.delete("/api/v1/groups/1")
        print(f"DELETE RESPONSE: {response.status_code}")
        assert response.status_code == status.HTTP_204_NO_CONTENT



