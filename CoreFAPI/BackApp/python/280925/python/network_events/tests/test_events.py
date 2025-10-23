import pytest
from httpx import AsyncClient
from app.main import app 
from app.schemas.event import EventCreate

event_data = {
    "title": "TEST_EVENT",
    "description": "DISC *NORM*",
    "location": "Ru"
}

# @pytest.mark.asyncio
# async def test_create_event(auth_client_MOCK: AsyncClient):

#     response = await auth_client_MOCK.post("/events/", json=event_data)
#     assert response.status_code == 200
#     data = response.json()
#     assert data["title"] == event_data["title"]
#     event_id = data["id"]
#     response = await auth_client_MOCK.delete(f"/events/{event_id}")
#     assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_event(auth_client_MOCK: AsyncClient, created_event):
    
    # create_response = await auth_client_MOCK.post("/events/", json=event_data)
    # assert create_response.status_code == 200

    event_id = created_event["id"]

    # Затем получаем его
    response = await auth_client_MOCK.get(f"/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["id"] == event_id


@pytest.mark.asyncio
async def test_list_events(auth_client_MOCK: AsyncClient):
    response = await auth_client_MOCK.get("/events/")
    print("GET EVENT RESPONSE555:", response.status_code, response.text)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_event(auth_client_MOCK: AsyncClient, created_event):
    # Создаём событие
    create_response = await auth_client_MOCK.post("/events/", json=event_data)
    print("sdasdas555",create_response.json())
    event_id = create_response.json()["id"]

    # Удаляем его
    response = await auth_client_MOCK.delete(f"/events/{event_id}")
    assert response.status_code == 204
