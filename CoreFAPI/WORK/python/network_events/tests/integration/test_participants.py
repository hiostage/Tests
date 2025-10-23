import pytest
from httpx import AsyncClient

payload = {
    "title": "ZXCZXC",
    "description": "ASDASD",
    "location": "Ru"
}

@pytest.mark.asyncio
async def test_all_participants(client: AsyncClient):
    response = await client.post("/events/", json = payload)
    assert response.status_code == 200

    event_id = response.json()["id"]
    
    response = await client.post("/register", json={"event_id": event_id})
    assert response.status_code == 200

    response = await client.get(f"/event/{event_id}/participants")
    assert response.status_code == 200

    response = await client.delete(f"/event/{event_id}/participant")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_for_event(client: AsyncClient):
    response = await client.post("/events/", json = payload)
    assert response.status_code == 200

    event_id = response.json()["id"]

    response = await client.post("/register", json={"event_id": event_id})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_register_for_event(client: AsyncClient):
    response = await client.post("/events/", json = payload)
    assert response.status_code == 200

    event_id = response.json()["id"]

    response = await client.post("/register", json={"event_id": event_id})
    assert response.status_code == 200

    response = await client.get(f"/event/{event_id}/participants")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_unregister_for_event(client: AsyncClient):
    response = await client.post("/events/", json = payload)
    assert response.status_code == 200

    event_id = response.json()["id"]

    response = await client.post("/register", json={"event_id": event_id})
    assert response.status_code == 200

    response = await client.delete(f"/event/{event_id}/participant")
    assert response.status_code == 200

