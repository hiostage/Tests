import pytest

from app.services.group import GroupService

from httpx import AsyncClient

from fastapi import Depends 

from sqlalchemy.ext.asyncio import AsyncSession

from unittest.mock import AsyncMock, patch, MagicMock

from app.schemas.group import GroupCreate, GroupUpdate, GroupWithMembers, GroupList

from app.models.group import Group

import uuid

GROUP_JSON = GroupCreate(
    name= "Test zxczxczx",
    category= "technology",
    is_public= True
)

user_uuid_MOCK = str(uuid.uuid4())

@pytest.mark.asyncio
async def test_create_group_unit():
    fake_db = AsyncMock()
    fake_execute_result = MagicMock()
    fake_execute_result.scalars.return_value.first.return_value = None
    fake_db.execute.return_value = fake_execute_result

    fake_db.add = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK
    fake_user.uuid = user_uuid_MOCK

    service = GroupService(fake_db, fake_user)

    with(
        patch("app.services.group.RabbitMQManager.publish_event", new=AsyncMock(return_value=None)),
        patch("app.services.group.cache.delete", new=AsyncMock(return_value=True)),
        patch.object(service, "add_member", new=AsyncMock(return_value=None)),
        patch("app.services.group.GroupWithMembers.from_group", return_value="mock_group")
    ):
        result = await service.create_group(GROUP_JSON, None)


    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once()
    assert result == "mock_group"

@pytest.mark.asyncio
async def test_add_member_to_group_unit():
    fake_db = AsyncMock()
    fake_db.get = AsyncMock(return_value=MagicMock())
    fake_db.refresh = AsyncMock()

    fake_group = MagicMock()
    fake_group.id = 1
    fake_db.get.return_value = fake_group

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK
    
    service = GroupService(fake_db, fake_user)

    with(
        patch("app.services.group.RabbitMQManager.publish_event", new = AsyncMock(return_value=None)) as mock_publish,
        patch("app.services.group.cache.delete", new = AsyncMock(return_value=True)),
        patch.object(service, "is_creator", new = AsyncMock(return_value=True)) as mock_is_creator,
        patch.object(service, "add_member", new = AsyncMock(return_value=None)) as mock_add_member,
        patch("app.services.group.GroupWithMembers.from_group", return_value="mock_group") as mock_from_group
    ): 
        result = await service.add_member_to_group(fake_group.id, fake_user.id)

    fake_db.get.assert_awaited_once_with(Group, fake_group.id)
    fake_db.refresh.assert_awaited_once_with(fake_group, ["creator", "members"])
    mock_is_creator.assert_awaited_once_with(fake_group.id, fake_user.id)
    mock_add_member.assert_awaited_once_with(fake_user.id, fake_group.id, "member")
    mock_publish.assert_awaited_once_with(event_type="user_added_to_group", payload={"group_id": fake_group.id, "uuid": fake_user.id}, routing_key="event.new_member")
    mock_from_group.assert_called_once_with(fake_group, user_id=fake_user.id, is_member=True)
    assert result == "mock_group"

@pytest.mark.asyncio
async def test_update_group_unit():
    fake_db = AsyncMock()

    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK

    fake_group = MagicMock()
    fake_group.id = 1 

    service = GroupService(fake_db, fake_user)

    with(
        patch.object(service, "is_creator", new=AsyncMock(return_value=fake_group)) as mock_is_creator,
        patch("app.services.group.cache.delete", new=AsyncMock(return_value=True)),
        patch("app.services.group.GroupWithMembers.from_group", return_value = "mock_group") as mock_from_group
    ):
        result = await service.update_group(fake_group.id, GROUP_JSON)

    mock_is_creator.assert_awaited_once_with(fake_group.id, fake_user.id)
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once_with(fake_group, attribute_names=["creator", "members"])
    mock_from_group.assert_called_once_with(fake_group, user_id=fake_user.id)

    assert result == "mock_group"

@pytest.mark.asyncio
async def test_get_groups_unit():
    fake_db = AsyncMock()

    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.all.return_value = [MagicMock()]
    fake_db_execute_result.scalar_one.return_value = 1
    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK

    service = GroupService(fake_db, fake_user)

    with(
        patch("app.services.group.GroupWithMembers.from_group", return_value="mock_group") as mock_from_group
    ):
        result = await service.get_groups()


    assert result["groups"][0] == "mock_group"
    assert result["total"] == 1
    assert result["limit"] == 100
    assert result["offset"] == 0

@pytest.mark.asyncio
async def test_get_group_unit():
    
    fake_db = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK

    fake_group = MagicMock()
    fake_group.id = 1

    service = GroupService(fake_db, fake_user)

    with (
        patch.object(service, "get_group_by_id", new=AsyncMock(return_value=fake_group)) as mock_get_group_by_id,
        patch.object(service, "is_member", new=AsyncMock(return_value=True)) as mock_is_member,
        patch("app.services.group.GroupWithMembers.from_group", return_value="mock_group") as mock_from_group
    ):
        result = await service.get_group(fake_group.id) 

    mock_get_group_by_id.assert_awaited_once_with(fake_group.id)
    mock_is_member.assert_awaited_once_with(fake_group.id, fake_user.id)
    mock_from_group.assert_called_once_with(fake_group, user_id=fake_user.id, is_member=True)
    assert result == "mock_group" 

@pytest.mark.asyncio
async def test_delete_group_unit():
    
    fake_db = AsyncMock()
    fake_db.delete = AsyncMock()
    fake_db.commit = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK

    fake_group = MagicMock()
    fake_group.id = 1

    service = GroupService(fake_db, fake_user)

    with (
        patch.object(service, "is_creator", new=AsyncMock(return_value=fake_group)) as mock_is_creator,
        patch("app.services.group.GroupWithMembers.from_group", return_value="mock_group")
    ):
        result = await service.delete_group(fake_group.id)

    fake_db.commit.assert_awaited_once()
    fake_db.delete.assert_awaited_once()
    mock_is_creator.assert_awaited_once_with(fake_group.id, fake_user.id)
    assert result == "mock_group"
    
@pytest.mark.asyncio
async def test_remove_member_from_group_unit():
    fake_db = AsyncMock()
    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.all.return_value = MagicMock()
    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = user_uuid_MOCK

    fake_group = MagicMock()
    fake_group.id = 1
    fake_group.members = []

    service = GroupService(fake_db, fake_user)

    with(
        patch.object(service, "is_creator", new=AsyncMock(return_value=fake_group)) as mock_is_creator,
        patch.object(service, "remove_member_pattern", new=AsyncMock(return_value=True)) as mock_remove_member_pattern,
        patch("app.services.group.GroupWithMembers.from_group", return_value="mock_group") as mock_from_group
    ):
        result = await service.remove_member(fake_group.id, fake_user.id)

    fake_db.execute.assert_awaited_once()

    mock_is_creator.assert_awaited_once_with(fake_group.id, fake_user.id)
    mock_remove_member_pattern.assert_awaited_once_with(fake_user.id, fake_group.id, fake_group)
    mock_from_group.assert_called_once_with(fake_group, user_id=fake_user.id, members=fake_group.members, is_member=False)

    assert result == "mock_group"

