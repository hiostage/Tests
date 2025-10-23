from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db

router = APIRouter()

@router.post("/like/")
async def like_post(like: schemas.LikeSchema, db: AsyncSession = Depends(get_db)):
    return await crud.add_like(db, like)

@router.post("/comment/")
async def comment_post(comment: schemas.CommentSchema, db: AsyncSession = Depends(get_db)):
    return await crud.add_comment(db, comment)

@router.post("/repost/")
async def repost_post(repost: schemas.RepostSchema, db: AsyncSession = Depends(get_db)):
    return await crud.add_repost(db, repost)
