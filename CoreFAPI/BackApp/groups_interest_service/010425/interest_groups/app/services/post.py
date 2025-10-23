from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate
from fastapi import HTTPException, status
from typing import List

def get_post(db: Session, post_id: int):
    return db.query(Post).filter(Post.id == post_id).first()

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Post).offset(skip).limit(limit).all()

def get_posts_by_group(db: Session, group_id: int, skip: int = 0, limit: int = 100):
    return db.query(Post).filter(Post.group_id == group_id).offset(skip).limit(limit).all()

def create_post(db: Session, post: PostCreate, author_id: int):
    db_post = Post(**post.dict(), author_id=author_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_post(db: Session, post_id: int, post: PostUpdate):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    update_data = post.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_post, field, update_data[field])
    
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, post_id: int):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    db.delete(db_post)
    db.commit()
    return db_post