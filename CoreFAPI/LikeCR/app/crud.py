from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas
from app.database import get_db


async def add_like(db: AsyncSession, like: schemas.LikeSchema):
    db_like = models.Like(**like.dict())
    db.add(db_like)
    await db.commit()
    await db.refresh(db_like)
    return db_like

async def add_comment(db: AsyncSession, comment: schemas.CommentSchema):
    db_comment = models.Comment(**comment.dict())
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

async def add_repost(db: AsyncSession, repost: schemas.RepostSchema):
    db_repost = models.Repost(**repost.dict())
    db.add(db_repost)
    await db.commit()
    await db.refresh(db_repost)
    return db_repost
