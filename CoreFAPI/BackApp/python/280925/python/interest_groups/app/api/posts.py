from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from app.schemas.post import PostWithAuthor, PostCreate, PostUpdate
from app.services.post import PostService
from app.db.session import get_db
from app.utils.auth import get_current_user
from app.schemas.user import UserPublic, UserFull
from fastapi_cache.decorator import cache

router = APIRouter(tags=["posts"])
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=PostWithAuthor,
    status_code=status.HTTP_201_CREATED
)
async def create_new_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserFull = Depends(get_current_user)
):
    """Создание нового поста в группе"""
    post_services = PostService(db, current_user)
    return await post_services.create_post(post_data=post)

@router.get("/", response_model=List[PostWithAuthor])
async def read_posts(
    skip: int = 0,
    limit: int = Query(default=100, le=500, description="Max 500 items"),
    db: AsyncSession = Depends(get_db),
    current_user: UserFull = Depends(get_current_user)
):
    """Получение всех постов с пагинацией"""
    post_services = PostService(db, current_user)
    return await post_services.get_posts(skip=skip, limit=limit)

@router.get("/group/{group_id}", response_model=List[PostWithAuthor])
@cache(expire=60)
async def read_posts_by_group(
    group_id: int, 
    skip: int = 0, 
    limit: int = Query(default=100, le=500), 
    db: AsyncSession = Depends(get_db), 
    current_user: UserFull = Depends(get_current_user)
):
    """Получение постов по ID группы"""
    post_services = PostService(db, current_user)
    return await post_services.get_posts_by_group(group_id=group_id, skip=skip, limit=limit)

@router.patch("/{post_id}", response_model=PostWithAuthor)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserFull = Depends(get_current_user),
):
    post_services = PostService(db, current_user)
    return await post_services.update_post(post_id=post_id, post_data=post_update)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserFull = Depends(get_current_user),
):
    post_services = PostService(db, current_user)
    await post_services.delete_post(post_id)

    return
