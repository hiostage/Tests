import pytest

from httpx import AsyncClient

NEW_GROUP = {
    "name": "UWU",
    "category": "technology",
    "is_public": True
}

NEW_POST = {
  "group_id": 1,
  "title": "Мой первый посsт",
  "content": "Это содержиsмое тестового поста."
}

PATCH_POST = {
  "title": "GGOSOSOSOS23",
  "content": "ASDASDASDASDASDAS."
}


@pytest.mark.asyncio
async def test_all_posts(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    group_id = response.json()["id"]

    response = await client.post("/api/v1/posts/", json={"group_id": group_id, "title": "Мой первый посsт", "content": "Это содержиsмое тестового поста."})

    assert response.status_code == 201
    post_id = response.json()["id"]

    response == await client.patch(f"/api/v1/posts/{post_id}", json=PATCH_POST)

    assert response.status_code == 201

    response = await client.get("/api/v1/posts/")

    assert response.status_code == 200

    response = await client.get(f"/api/v1/posts/group/{group_id}")

    assert response.status_code == 200

    response = await client.delete(f"/api/v1/posts/{post_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_posts(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    group_id = response.json()["id"]

    response = await client.post("/api/v1/posts/", json={"group_id": group_id, "title": "Мой первый посsт", "content": "Это содержиsмое тестового поста."})

    assert response.status_code == 201

@pytest.mark.asyncio
async def test_patch_posts(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    group_id = response.json()["id"]

    response = await client.post("/api/v1/posts/", json={"group_id": group_id, "title": "Мой первый посsт", "content": "Это содержиsмое тестового поста."})

    assert response.status_code == 201
    post_id = response.json()["id"]

    response == await client.patch(f"/api/v1/posts/{post_id}", json=PATCH_POST)

    assert response.status_code == 201

@pytest.mark.asyncio
async def test_get_all_posts(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    group_id = response.json()["id"]

    response = await client.post("/api/v1/posts/", json={"group_id": group_id, "title": "Мой первый посsт", "content": "Это содержиsмое тестового поста."})

    assert response.status_code == 201

    response = await client.get("/api/v1/posts/")

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_posts_by_id_group(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    group_id = response.json()["id"]

    response = await client.post("/api/v1/posts/", json={"group_id": group_id, "title": "Мой первый посsт", "content": "Это содержиsмое тестового поста."})

    assert response.status_code == 201

    response = await client.get(f"/api/v1/posts/group/{group_id}")

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_posts(client: AsyncClient):
    response = await client.post("/api/v1/groups/", json=NEW_GROUP)

    assert response.status_code == 201
    group_id = response.json()["id"]

    response = await client.post("/api/v1/posts/", json={"group_id": group_id, "title": "Мой первый посsт", "content": "Это содержиsмое тестового поста."})

    assert response.status_code == 201
    post_id = response.json()["id"]

    response = await client.delete(f"/api/v1/posts/{post_id}")

    assert response.status_code == 204
