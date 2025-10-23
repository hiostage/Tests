import pytest
from httpx import AsyncClient
from app.main import app  # Или где у тебя FastAPI-приложение
from app.schemas.event import EventCreate


@pytest.mark.asyncio
async def test_create_event(async_client: AsyncClient):
    event_data = {
        "title": "Тестовое событие",
        "description": "Описание события",
        "date": "2025-05-01T10:00:00Z"
    }
    response = await async_client.post("/events/", json=event_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == event_data["title"]


@pytest.mark.asyncio
async def test_get_event(async_client: AsyncClient):
    # Сначала создаём событие
    create_response = await async_client.post("/events/", json={
        "title": "Для получения",
        "description": "Тест",
        "date": "2025-06-01T10:00:00Z"
    })
    event_id = create_response.json()["id"]

    # Затем получаем его
    response = await async_client.get(f"/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id


@pytest.mark.asyncio
async def test_list_events(async_client: AsyncClient):
    response = await async_client.get("/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_event(async_client: AsyncClient):
    # Создаём событие
    create_response = await async_client.post("/events/", json={
        "title": "На удаление",
        "description": "Тест",
        "date": "2025-07-01T10:00:00Z"
    })
    event_id = create_response.json()["id"]

    # Удаляем его
    response = await async_client.delete(f"/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id
