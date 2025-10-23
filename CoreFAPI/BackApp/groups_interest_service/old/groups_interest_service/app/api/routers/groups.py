from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models, schemas, crud
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.GroupResponse)
async def create_group(group: schemas.GroupCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_group(db, group)

@router.get("/{group_id}", response_model=schemas.GroupResponse)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await crud.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group