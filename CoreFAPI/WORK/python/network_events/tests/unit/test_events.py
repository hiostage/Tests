import pytest

from unittest.mock import AsyncMock, MagicMock, patch

from uuid import uuid4

from app.services.events import EventService

from app.schemas.event import EventCreate

fake_user_uuid = str(uuid4())

event_data_MOCK = EventCreate(
    title= "ZXCZXC",
    description= "ASDASD",
    location= "Ru"
)

@pytest.mark.asyncio
async def test_create_event_unit():

    fake_db = AsyncMock()
    fake_db.add = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid

    fake_event_data= MagicMock()
    fake_event_data.model_dump.return_value = {"name": "Test event", "location": "Almaty"}

    service = EventService(fake_db, fake_user)

    mock_event_instance = MagicMock()

    with (
        patch("app.services.events.send_event_event", new=AsyncMock(return_value=True)) as mock_send_event_event,
        patch("app.services.events.Event", return_value=mock_event_instance) as mock_Event,
    ):
        result = await service.create_event(fake_event_data)

    mock_Event.assert_called_once_with(**fake_event_data.model_dump.return_value)
    mock_send_event_event.assert_awaited_once()

    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once()

    assert result == mock_event_instance

@pytest.mark.asyncio
async def test_get_event_unit():

    fake_db = AsyncMock()
    fake_db_execute_result = MagicMock()

    fake_event = MagicMock()
    fake_event.id = 1 

    fake_db_execute_result.scalar_one_or_none.return_value = fake_event

    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid

    service = EventService(fake_db, fake_user)

    result = await service.get_event(fake_event.id)

    fake_db.execute.assert_awaited_once()

    assert result == fake_event

@pytest.mark.asyncio
async def test_list_events_unit():

    fake_db = AsyncMock()

    fake_event = MagicMock()

    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.all.return_value = [fake_event]
    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid

    service = EventService(fake_db, fake_user)

    result = await service.list_events()    
    
    fake_db.execute.assert_awaited_once()

    assert result == [fake_event]


@pytest.mark.asyncio 
async def test_delete_event_unit():

    fake_db = AsyncMock()
    
    fake_db.delete = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.execute = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid

    fake_event = MagicMock()
    fake_event.id = 1

    service = EventService(fake_db, fake_user)

    with(
        patch.object(service, "get_event", new=AsyncMock(return_value=fake_event)) as mock_get_event,
        patch("app.services.events.send_event_event", new=AsyncMock(return_value=True)) as mock_send_event
    ):
        result = await service.delete_event(fake_event.id)

    fake_db.commit.assert_awaited_once()
    fake_db.delete.assert_awaited_once()
    fake_db.execute.assert_awaited_once()
    
    mock_get_event.assert_awaited_once_with(fake_event.id)
    mock_send_event.assert_awaited_once_with(fake_event.id, "event_deleted")

    assert result == fake_event
