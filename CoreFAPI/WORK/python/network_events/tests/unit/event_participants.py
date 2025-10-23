import pytest

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.participants import ParticipantService

from uuid import uuid4

fake_user_uuid = str(uuid4())

@pytest.mark.asyncio
async def test_register_user_to_event_unit():
    
    fake_db = AsyncMock()

    fake_event = MagicMock()
    fake_event.id = 1 

    fake_db.add = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()
    fake_db.get.return_value = fake_event

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid

    fake_registrations = MagicMock()
    fake_registrations.event_id = 2


    mock_registration_instance = MagicMock()
    mock_registration_instance.event_id = 2

    service = ParticipantService(fake_db, fake_user)

    with(
        patch("app.services.participants.EventRegistration", return_value=mock_registration_instance) as mock_event_registrations,
        patch.object(service, "is_registered", new=AsyncMock(return_value=False)) as mock_is_registered,
        patch("app.services.participants.send_participant_event", new=AsyncMock(return_value=True)) as mock_send_participant_event,
    ):
        result = await service.register_user_to_event(fake_registrations)

    mock_event_registrations.assert_called_once()
    mock_is_registered.assert_awaited_once_with(mock_registration_instance.event_id)
    mock_send_participant_event.assert_awaited_once_with("user_registered", fake_registrations.event_id, fake_user.id)

    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once()
    fake_db.get.assert_awaited_once()

    assert result == mock_registration_instance

@pytest.mark.asyncio
async def test_get_participants_for_event_unit():

    fake_db = AsyncMock()

    fake_event = MagicMock()
    fake_event.id = 1

    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.all.return_value = [fake_event]
    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid


    service = ParticipantService(fake_db, fake_user)

    result = await service.get_participants_for_event(fake_event.id)

    fake_db.execute.assert_awaited_once()
    assert result == [fake_event]

@pytest.mark.asyncio
async def test_remove_participant_from_event_unit():
    
    fake_db = AsyncMock()

    fake_db.delete = AsyncMock()
    fake_db.commit = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = fake_user_uuid

    fake_event = MagicMock()
    fake_event.id = 1 
    fake_event.event_id = 2
    service = ParticipantService(fake_db, fake_user)

    with(
        patch.object(service, "is_registered", new=AsyncMock(return_value=fake_event)) as mock_is_registered,
        patch("app.services.participants.send_participant_event", new=AsyncMock(retunr_value=None)) as mock_send_participant_event,
    ):
        result = await service.remove_participant_from_event(fake_event.id)

    mock_is_registered.assert_awaited_once_with(fake_event.id)
    mock_send_participant_event.assert_awaited_once_with("user_unregistered", fake_event.event_id, fake_user.id)

    fake_db.delete.assert_awaited_once()
    fake_db.commit.assert_awaited_once()

    assert result == fake_event
