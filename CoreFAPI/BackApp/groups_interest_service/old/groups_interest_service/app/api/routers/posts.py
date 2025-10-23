from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models, schemas, crud
from app.db.session import get_db

# Создаём роутер
router = APIRouter()

@router.post("/", response_model=schemas.PostResponse)
async def create_post(
    post: schemas.PostCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание нового поста в группе"""
    return await crud.create_post(db, post)

@router.get("/{post_id}", response_model=schemas.PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение поста по ID"""
    post = await crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post