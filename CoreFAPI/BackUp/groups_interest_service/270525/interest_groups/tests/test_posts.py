from app.schemas.post import PostWithAuthor
import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, AsyncMock
from app.models.user import User
from app.schemas.user import UserPublic
from app.models.group import Group
from datetime import datetime

from app.models import Post



@pytest.mark.asyncio
async def test_create_post(auth_client: AsyncClient, mock_group: Group, mock_creator: User):
    post_data = {
        "group_id": mock_group.id,
        "title": "Test Post",
        "content": "This is a test post."
    }

    mock_post = PostWithAuthor(
        id=1,
        group_id=mock_group.id,
        title=post_data["title"],
        content=post_data["content"],
        author_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        author=UserPublic.from_orm(mock_creator)
    )

    with (
        patch("app.services.group.group_members", new_callable=AsyncMock),
        patch("app.api.posts.is_group_member", AsyncMock(return_value=True)),
        patch("app.services.post.PostService.create_post", AsyncMock(return_value=mock_post)),
        patch("app.utils.auth.get_current_user_for_posts", AsyncMock(return_value=UserPublic.from_orm(mock_creator))),
    ):
        response = await auth_client.post("/api/v1/posts/", json=post_data)

    assert response.status_code == 201
    result = response.json()
    assert result["title"] == post_data["title"]
    assert result["author"]["id"] == mock_creator.id

@pytest.mark.asyncio
async def test_get_all_posts(auth_client: AsyncClient, mock_creator: User):
    mock_post = PostWithAuthor(
        id=1,
        group_id=1,
        title="Test",
        content="Test content",
        author_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        author=UserPublic.from_orm(mock_creator)
    )

    with patch("app.services.post.PostService.get_posts", AsyncMock(return_value=[mock_post])):
        response = await auth_client.get("/api/v1/posts/")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["title"] == "Test"

@pytest.mark.asyncio
async def test_update_post(auth_client: AsyncClient, mock_creator: User):
    updated_post = PostWithAuthor(
        id=1,
        group_id=1,
        title="Updated title",
        content="Updated content",
        author_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        author=UserPublic.from_orm(mock_creator)
    )

    with (
        patch("app.services.post.PostService.get_post_by_id", AsyncMock(return_value=updated_post)),
        patch("app.services.post.PostService.update_post", AsyncMock(return_value=updated_post)),
        patch("app.utils.auth.get_current_user_for_posts", AsyncMock(return_value=UserPublic.from_orm(mock_creator)))
    ):
        response = await auth_client.patch("/api/v1/posts/1", json={"title": "Updated title"})

    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"

@pytest.mark.asyncio
async def test_delete_post(auth_client: AsyncClient, mock_creator: User):
    mock_post = Post(  # Используем базовую модель вместо PostWithAuthor
        id=1,
        group_id=1,
        title="Test",
        content="Test",
        author_id=mock_creator.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    with (
        patch("app.services.post.PostService.get_post_by_id", AsyncMock(return_value=mock_post)),
        patch("app.services.post.PostService.delete_post", AsyncMock()),
        patch("app.utils.auth.get_current_user_for_posts", 
             AsyncMock(return_value={"id": mock_creator.id})),  # Упрощаем мок пользователя
    ):
        response = await auth_client.delete("/api/v1/posts/1")
    
    assert response.status_code == 204