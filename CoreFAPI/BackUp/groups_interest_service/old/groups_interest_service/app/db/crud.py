from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models, schemas

async def create_group(db: AsyncSession, group: schemas.GroupCreate):
    db_group = models.Group(**group.dict())
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    return db_group

async def get_group(db: AsyncSession, group_id: int):
    return await db.get(models.Group, group_id)

async def create_post(db: AsyncSession, post: schemas.PostCreate):
    db_post = models.Post(**post.dict())
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post

async def get_post(db: AsyncSession, post_id: int):
    return await db.get(models.Post, post_id)

async def create_comment(db: AsyncSession, comment: schemas.CommentCreate):
    db_comment = models.Comment(**comment.dict())
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

async def get_comment(db: AsyncSession, comment_id: int):
    return await db.get(models.Comment, comment_id)