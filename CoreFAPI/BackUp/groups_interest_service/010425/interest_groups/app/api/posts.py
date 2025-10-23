from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.post import Post, PostCreate, PostUpdate
from app.services.post import (
    get_post, get_posts, create_post, 
    update_post, delete_post, get_posts_by_group
)
from app.db.session import get_db
from app.utils.auth import get_current_user
from app.schemas.user import User

router = APIRouter()

@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_new_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать новый пост в группе"""
    return create_post(db=db, post=post, author_id=current_user.id)

@router.get("/", response_model=List[Post])
def read_posts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Получить список всех постов"""
    return get_posts(db, skip=skip, limit=limit)

@router.get("/group/{group_id}", response_model=List[Post])
def read_posts_by_group(
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить посты конкретной группы"""
    return get_posts_by_group(db, group_id=group_id, skip=skip, limit=limit)

@router.get("/{post_id}", response_model=Post)
def read_post(
    post_id: int, 
    db: Session = Depends(get_db)
):
    """Получить конкретный пост"""
    db_post = get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@router.put("/{post_id}", response_model=Post)
def update_existing_post(
    post_id: int,
    post: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить пост"""
    db_post = get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can update the post")
    return update_post(db=db, post_id=post_id, post=post)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить пост"""
    db_post = get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only author can delete the post")
    delete_post(db=db, post_id=post_id)
    return {"ok": True}