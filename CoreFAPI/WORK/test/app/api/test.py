from fastapi import APIRouter, Depends
from app.schema.test_schema import Test_schema
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from app.db.database import get_db

from app.models.id import Iddd
router = APIRouter()


@router.post("/", response_model=Test_schema)
async def get_value(event: Test_schema, db: AsyncSession = Depends(get_db)):
    event_dump = Iddd(**event.model_dump())
    db.add(event_dump)
    await db.commit()
    return event


@router.get("/get", response_model= list[Test_schema])
async def get(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Iddd))
    take = result.scalars().all() 
    return take