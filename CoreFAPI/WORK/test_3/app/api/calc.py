from fastapi import APIRouter, Depends

from app.scheme.scheme import calc_Scheme, calc_Result, calc_With_ID, Calc_Upgrade, Calc_Scheme_Delete

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db

from app.models.calc_model import Calc_Model

from app.services.calc import Clalc_logic

router = APIRouter()

@router.post('/')
async def calc(event: calc_Scheme, db: AsyncSession = Depends(get_db)):

    event_dump = await Clalc_logic.Sum(val_1=event.val_1, val_2=event.val_2)
    
    db.add(event_dump)
    await db.commit()

    return event_dump


@router.get('/get', response_model=list[calc_With_ID])
async def get_value(db: AsyncSession = Depends(get_db)):
    logic = Clalc_logic(db)
    return await logic.get_value()

@router.put('/put')
async def update_value(event: Calc_Upgrade, db: AsyncSession = Depends(get_db)):
    logic = Clalc_logic(db, event)
    return await logic.calc_put()

@router.delete('/delete')
async def calc_delete(event: Calc_Scheme_Delete, db: AsyncSession = Depends(get_db)):
    result = Clalc_logic(db, event)
    return await result.calc_delete()


@router.delete('/delete_all')
async def calc_delete_all(db: AsyncSession = Depends(get_db)):
    logic = Clalc_logic(db)

    return await logic.calc_delete_all()


@router.get('/get-by-id/{id}')
async def get_by_id(id:int, db: AsyncSession = Depends(get_db)):
    stmt = select(Calc_Model).filter(Calc_Model.id == id)
    result = await db.execute(stmt)
    obj = result.scalars().first()

    return obj
