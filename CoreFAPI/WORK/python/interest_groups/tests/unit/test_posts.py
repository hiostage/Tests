import pytest

from app.services.post import PostService

from unittest.mock import AsyncMock, MagicMock, patch

from uuid import uuid4

from app.schemas.group import GroupCreate
from app.schemas.post import PostCreate

user_uuid = str(uuid4())

post_data_MOCK = PostCreate(
  group_id= 1,
  title= "Мой первый посsт",
  content= "Это содержиsмое тестового поста."
)

GROUP_JSON = GroupCreate(
    name= "Test zxczxczx",
    category= "technology",
    is_public= True
)

@pytest.mark.asyncio
async def test_create_post_unit():
    fake_db = AsyncMock()
    fake_db.add = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    fake_user= MagicMock()
    fake_user.id = user_uuid

    fake_group = MagicMock()
    fake_group.id = 1 

    service = PostService(fake_db, fake_user)

    with(
        patch.object(service, "get_group_by_id", new=AsyncMock(return_value=GROUP_JSON)) as mock_get_group_by_id,
        patch.object(service, "is_group_member", new=AsyncMock(return_value=GROUP_JSON)) as mock_is_group_member,
        patch("app.services.post.PostWithAuthor.from_orm",return_value="mock_post") as mock_from_orm,
        patch("app.services.post.RabbitMQManager.publish_event", new=AsyncMock(return_value=None)) as mock_publish_event
    ):
        result = await service.create_post(post_data_MOCK)

    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once()
    fake_db.add.assert_called_once()

    mock_get_group_by_id.assert_awaited_once_with(post_data_MOCK.group_id)
    mock_is_group_member.assert_awaited_once_with(fake_user.id ,post_data_MOCK.group_id)
    mock_publish_event.assert_awaited_once()
    mock_from_orm.assert_called_once()

    assert result == "mock_post"
        
@pytest.mark.asyncio
async def test_update_post_unit():

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = user_uuid
    
    fake_group = MagicMock()
    fake_group.id = 1

    fake_post = MagicMock()
    fake_post.id = 1 

    service = PostService(fake_db, fake_user)

    with(
        patch.object(service, "is_author", new=AsyncMock(return_value=fake_post)) as mock_is_author,
        patch("app.services.post.PostWithAuthor.from_orm", return_value="mock_post") as mock_from_orm,
    ):
        result = await service.update_post(fake_post.id, post_data_MOCK)

    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once()
    mock_is_author.assert_awaited_once_with(fake_post.id)
    mock_from_orm.assert_called_once_with(fake_post)
    assert result == "mock_post"

@pytest.mark.asyncio
async def test_get_posts_unit():

    fake_db = AsyncMock()

    fake_post = MagicMock()
    fake_post.id = 1 

    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.all.return_value = [fake_post]
    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = user_uuid

    service = PostService(fake_db, fake_user)

    with(
        patch("app.services.post.PostWithAuthor.from_orm", return_value="mock_post") as mock_from_orm,
    ):
        result = await service.get_posts()

    fake_db.execute.assert_awaited_once()
    mock_from_orm.assert_called_once_with(fake_post)
    assert result == ["mock_post"]

@pytest.mark.asyncio
async def test_get_posts_by_group_unit():
    
    fake_db = AsyncMock()

    fake_post = MagicMock()
    fake_post.id = 1


    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.all.return_value = [fake_post]
    fake_db.execute.return_value = fake_db_execute_result

    fake_user = MagicMock()
    fake_user.id = user_uuid


    fake_group = MagicMock()
    fake_group.id = 1

    service = PostService(fake_db, fake_user)

    with (
        patch.object(service, "get_group_by_id", new=AsyncMock(return_value=True)) as mock_get_group_by_id,
        patch("app.services.post.PostWithAuthor.from_orm", return_value="mock_post") as mock_from_orm
    ):
        result = await service.get_posts_by_group(fake_group.id)
    
    fake_db.execute.assert_awaited_once()
    mock_get_group_by_id.assert_awaited_once_with(fake_group.id)
    mock_from_orm.assert_called_once_with(fake_post)
    assert result == ["mock_post"]


@pytest.mark.asyncio
async def test_get_post_unit():

    fake_db = AsyncMock()

    fake_post = MagicMock()
    fake_post.id = 1 

    fake_db_execute_result = MagicMock()
    fake_db_execute_result.scalars.return_value.first.return_value = fake_post
    fake_db.execute.return_value = fake_db_execute_result 

    fake_user = MagicMock()
    fake_user.id = user_uuid

    service = PostService(fake_db, fake_user)

    with(
        patch("app.services.post.PostWithAuthor.from_orm", return_value="mock_post") as mock_from_orm,
    ):
        result = await service.get_post(fake_post.id)

    fake_db.execute.assert_awaited_once()
    mock_from_orm.assert_called_once_with(fake_post)
    assert result == "mock_post"

@pytest.mark.asyncio
async def test_delete_post_unit():

    fake_db = AsyncMock()
    fake_db.commit = AsyncMock()
    fake_db.execute.return_value = AsyncMock()

    fake_user = MagicMock()
    fake_user.id = user_uuid

    fake_post = MagicMock()
    fake_post.id = 1 

    service = PostService(fake_db, fake_user)

    with(
        patch("app.services.post.PostWithAuthor.from_orm", return_value="mock_post") as mock_from_orm,
        patch.object(service, "is_author", new=AsyncMock(return_value=fake_post)) as mock_is_author
    ):
        result = await service.delete_post(fake_post.id)

    fake_db.commit.assert_awaited_once()
    fake_db.execute.assert_awaited_once()
    mock_from_orm.assert_called_once_with(fake_post)
    mock_is_author.assert_awaited_once_with(fake_post.id)
    assert result == "mock_post"
    