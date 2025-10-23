import pytest
from httpx import AsyncClient
from fastapi import FastAPI

# Допустим, ты работаешь с app.main.app
from app.main import app


@pytest.mark.asyncio
async def test_register_for_event(client_with_auth: AsyncClient, override_user_dependency):
    create_event = await client_with_auth.post("/events/", json={
        "title": "Регистрация на событие",
        "description": "Тест регистрации",
        "date": "2025-05-15T12:00:00Z"
    })
    event_id = create_event.json()["id"]

    response = await client_with_auth.post("/register", json={
        "event_id": event_id
    })

    assert response.status_code == 200
    assert response.json()["event_id"] == event_id
    assert response.json()["user_id"] == 1





@pytest.mark.asyncio
async def test_get_event_participants(async_client: AsyncClient):
    headers = {"Cookie": "session_id=test_session"}

    # Создаём событие
    event = await async_client.post("/events/", json={
        "title": "Участники",
        "description": "Тест",
        "date": "2025-06-01T10:00:00Z"
    }, headers=headers)
    event_id = event.json()["id"]

    # Регистрируемся
    await async_client.post("/register", json={"event_id": event_id}, headers=headers)

    # Получаем участников
    response = await async_client.get(f"/event/{event_id}/participants", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(part["user_id"] == 1 for part in data)  # если в mock id = 1



@pytest.mark.asyncio
async def test_remove_participant(async_client: AsyncClient):
    headers = {"Cookie": "session_id=test_session"}

    # Создаём событие
    event = await async_client.post("/events/", json={
        "title": "Удаление участника",
        "description": "Тест",
        "date": "2025-06-10T10:00:00Z"
    }, headers=headers)
    event_id = event.json()["id"]

    # Регистрируемся на событие
    await async_client.post("/register", json={"event_id": event_id}, headers=headers)

    # Удаляем участника
    response = await async_client.delete(f"/event/{event_id}/participant", headers=headers)
    assert response.status_code == 200
    assert response.json()["user_id"] == 1  # если у тебя в mock_auth id = 1

