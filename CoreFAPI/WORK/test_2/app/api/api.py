from fastapi import APIRouter, Depends
from app.scheme.scheme import Proba, Calc, Calc_with_id
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select 

from app.db.database import get_db
from app.model.model import Sum

router = APIRouter()


@router.post('/', response_model=Calc)
async def calc(event: Proba, db: AsyncSession = Depends(get_db)):
    a= event.a
    b= event.b
    result = a+b 
    event_dump = Sum(a=a, b=b, result=result)
    db.add(event_dump)
    await db.commit()
    return event_dump


@router.get('/get', response_model=list[Calc_with_id])
async def GetSum(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Sum))
    take = result.scalars().all()
    return take