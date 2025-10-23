import pytest
from httpx import AsyncClient
from fastapi import FastAPI

# Допустим, ты работаешь с app.main.app
from app.main import app


@pytest.mark.asyncio
async def test_register_for_event(auth_client_MOCK: AsyncClient, override_user_dependency):
    create_event = await auth_client_MOCK.post("/events/", json={
        "title": "Регистрация на событие",
        "description": "Тест регистрации",
        "date": "2025-05-15T12:00:00Z"
    })
    event_id = create_event.json()["uuid"]

    response = await auth_client_MOCK.post("/register", json={
        "event_id": event_id
    })

    print("print(response.text):",response.text)
    assert response.status_code == 200
    assert response.json()["event_id"] == event_id




#### Только с реальной сессией ####
# @pytest.mark.asyncio
# async def test_get_event_participants(client_with_auth: AsyncClient):

#     # Создаём событие
#     event = await client_with_auth.post("/events/", json={
#         "title": "Участники",
#         "description": "Тест",
#         "date": "2025-06-01T10:00:00Z"
#     })
#     print("Response from create event:", event.status_code, event.text)
#     event_id = event.json()["id"]
#     # Регистрируемся
#     await client_with_auth.post("/register", json={"event_id": event_id})
    
#     # Получаем участников
#     response = await client_with_auth.get(f"/event/{event_id}/participants")
#     assert response.status_code == 200
#     data = response.json()
#     assert isinstance(data, list)



# @pytest.mark.asyncio
# async def test_remove_participant(client_with_auth: AsyncClient):

#     # Создаём событие
#     event = await client_with_auth.post("/events/", json={
#         "title": "Удаление участника",
#         "description": "Тест",
#         "date": "2025-06-10T10:00:00Z"
#     })
#     event_id = event.json()["id"]

#     # Регистрируемся на событие
#     await client_with_auth.post("/register", json={"event_id": event_id})

#     # Удаляем участника
#     response = await client_with_auth.delete(f"/event/{event_id}/participant")
#     assert response.status_code == 200

#### Только с реальной сессией ####