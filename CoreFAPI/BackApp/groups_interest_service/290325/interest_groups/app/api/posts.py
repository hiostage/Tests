from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.schemas.post import Post, PostCreate, PostUpdate
from app.services.post import (
    get_post, get_posts, create_post, 
    update_post, delete_post, get_posts_by_group
)
from app.db.session import get_db
from app.utils.auth import get_current_user
from app.schemas.user import User
from fastapi_cache.decorator import cache

router = APIRouter(tags=["posts"])
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=Post,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Post created successfully"},
        400: {"description": "Invalid input data"},
        403: {"description": "Not authorized or not a group member"},
        404: {"description": "Group not found"}
    }
)
def create_new_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new post in a group
    
    - **group_id**: required
    - **title**: min 3 chars, max 100 chars
    - **content**: min 10 chars
    """
    if not is_group_member(db, post.group_id, current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You must be a group member to create posts"
        )
    try:
        return create_post(db=db, post=post, author_id=current_user.id)
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not create post")

@router.get("/", response_model=List[Post])
def read_posts(
    skip: int = 0,
    limit: int = Query(default=100, le=500, description="Max 500 items"),
    db: Session = Depends(get_db)
):
    """Get all posts with pagination"""
    return get_posts(db, skip=skip, limit=limit)

@router.get(
    "/group/{group_id}",
    response_model=List[Post],
    responses={404: {"description": "Group not found"}}
)
@cache(expire=60)
def read_posts_by_group(
    group_id: int,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db)
):
    """Get posts by group ID"""
    return get_posts_by_group(db, group_id=group_id, skip=skip, limit=limit)

# ... остальные методы с аналогичными улучшениями ...