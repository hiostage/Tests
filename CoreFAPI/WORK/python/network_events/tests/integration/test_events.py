import pytest
from httpx import AsyncClient

payload = {
    "title": "ZXCZXC",
    "description": "ASDASD",
    "location": "Ru"
}


@pytest.mark.asyncio
async def test_all_event(client: AsyncClient):

    response = await client.post("/events/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    event_id = data["id"]

    response = await client.get("/events/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == payload["title"]
    assert data[0]["description"] == payload["description"]

    response = await client.get(f"/events/{event_id}")
    assert response.status_code == 200

    response = await client.delete(f"/events/{event_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_events(client: AsyncClient):
    response = await client.get("/events/")
    
    assert response.status_code == 200
    

@pytest.mark.asyncio
async def test_get_event_by_id(client: AsyncClient):
    response = await client.post("/events/", json=payload)
    assert response.status_code == 200

    event_id = response.json()["id"]

    response = await client.get(f"/events/{event_id}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_event_delete(client: AsyncClient):
    response = await client.post("/events/", json=payload)
    assert response.status_code == 200

    event_id = response.json()["id"]

    response = await client.delete(f"/events/{event_id}")

    assert response.status_code == 204
