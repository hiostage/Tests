from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.models.group import group_members
from app.schemas.post import PostWithAuthor, PostCreate, PostUpdate
from app.services.post import PostService
from app.db.session import get_db
from app.utils.auth import get_current_user_for_posts
from app.schemas.user import UserPublic
from fastapi_cache.decorator import cache

router = APIRouter(tags=["posts"])
logger = logging.getLogger(__name__)

async def is_group_member(db: AsyncSession, group_id: int, user_id: str) -> bool:
    """Проверяет, является ли пользователь членом группы (асинхронно)"""
    result = await db.execute(
        select(group_members.c.user_id)
        .where(
            (group_members.c.group_id == group_id) & 
            (group_members.c.user_id == user_id)
        )
    )
    return result.scalar() is not None

@router.post(
    "/",
    response_model=PostWithAuthor,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Post created successfully"},
        400: {"description": "Invalid input data"},
        403: {"description": "Not authorized or not a group member"},
        404: {"description": "Group not found"}
    }
)
async def create_new_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user_for_posts)
):
    """Создание нового поста в группе"""
    if not await is_group_member(db, post.group_id, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You must be a group member to create posts"
        )
    
    post_services = PostService(db)

    try:
        return await post_services.create_post(post_data=post, author_id=current_user.id)
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not create post")

@router.get("/", response_model=List[PostWithAuthor])
async def read_posts(
    skip: int = 0,
    limit: int = Query(default=100, le=500, description="Max 500 items"),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех постов с пагинацией"""
    post_services = PostService(db)
    return await post_services.get_posts(skip=skip, limit=limit)

@router.get(
    "/group/{group_id}",
    response_model=List[PostWithAuthor],
    responses={404: {"description": "Group not found"}}
)
@cache(expire=60)
async def read_posts_by_group(
    group_id: int,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Получение постов по ID группы"""
    post_services = PostService(db)
    # Проверяем, существует ли группа
    group_exists = await db.execute(select(group_members.c.group_id).where(group_members.c.group_id == group_id))
    if not group_exists.scalar():
        raise HTTPException(status_code=404, detail="Group not found")

    return await post_services.get_posts_by_group(group_id=group_id, skip=skip, limit=limit)

@router.patch("/{post_id}", response_model=PostWithAuthor)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user_for_posts),
):
    post_services = PostService(db)
    post = await post_services.get_post_by_id(post_id)  # Получаем пост по ID
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    updated_post = await post_services.update_post(post_id=post_id, post_data=post_update,)
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserPublic = Depends(get_current_user_for_posts),
):
    post_services = PostService(db)
    post = await post_services.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    await post_services.delete_post(post_id)
    return {"detail": "Post deleted successfully"}
