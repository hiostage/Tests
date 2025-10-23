import pytest
from httpx import AsyncClient
import uuid
NEW_GROUP = {
    "name": "UWU",
    "category": "technology",
    "is_public": True
}

RENAME_GROUP = {
    "name": "UWU3",
    "category": "technology",
    "is_public": True
}

second_user_id = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_all_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    assert response.json()["name"] == NEW_GROUP["name"]

    group_id = response.json()["id"]

    response = await client.put(f"/api/v1/groups/{group_id}", json=RENAME_GROUP)

    assert response.status_code == 200
    assert response.json()["name"] == RENAME_GROUP["name"]
    assert response.json()["id"] == group_id

    response = await client.post(f"/api/v1/groups/{group_id}/members/{second_user_id}")

    assert response.status_code == 200
    assert response.json()["member_count"] == 2

    response = await client.get(f"/api/v1/groups/{group_id}")

    assert response.status_code == 200
    assert response.json()["name"] == RENAME_GROUP["name"]

    response = await client.delete(f"/api/v1/groups/{group_id}/members/{second_user_id}")

    assert response.status_code == 204

    response = await client.delete(f"/api/v1/groups/{group_id}")
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_create_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_put_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)
    assert response.status_code == 201

    group_id = response.json()["id"]

    response = await client.put(f"/api/v1/groups/{group_id}", json=RENAME_GROUP)

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_add_and_remove_member_to_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)
    assert response.status_code == 201

    group_id = response.json()["id"]

    response = await client.post(f"/api/v1/groups/{group_id}/members/{second_user_id}")

    assert response.status_code == 200

    response = await client.delete(f"/api/v1/groups/{group_id}/members/{second_user_id}")

    assert response.status_code == 204

@pytest.mark.asyncio
async def test_get_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)
    assert response.status_code == 201

    group_id = response.json()["id"]

    response = await client.get(f"/api/v1/groups/{group_id}")

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)
    assert response.status_code == 201

    group_id = response.json()["id"]

    response = await client.delete(f"/api/v1/groups/{group_id}")

    assert response.status_code == 204