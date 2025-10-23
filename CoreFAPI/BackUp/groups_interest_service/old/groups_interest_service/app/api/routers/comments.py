from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models, schemas, crud
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.CommentResponse)
async def create_comment(
    comment: schemas.CommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание комментария к посту"""
    return await crud.create_comment(db, comment)

@router.get("/{comment_id}", response_model=schemas.CommentResponse)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение комментария по ID"""
    comment = await crud.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment