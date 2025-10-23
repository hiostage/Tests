from app.scheme.scheme import calc_Result
from app.models.calc_model import Calc_Model
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database.database import get_db

class Clalc_logic():
    def __init__(self, db: AsyncSession, event=None):
        self.db = db
        self.event = event

    @staticmethod
    async def Sum(val_1, val_2):
        result = val_1 + val_2

        return Calc_Model(val_1=val_1, val_2=val_2, result=result)
    
    async def get_value(self):
        result= await self.db.execute(select(Calc_Model))
        take = result.scalars().all()

        return take
    
    async def calc_put(self):
        stmt = select(Calc_Model).filter(Calc_Model.id == self.event.id)
        result = await self.db.execute(stmt)
        obj = result.scalars().first()

        obj.val_1 = self.event.val_1
        obj.val_2 = self.event.val_2
        obj.result = self.event.val_1 + self.event.val_2

        await self.db.commit()
        await self.db.refresh(obj)

        return obj
    
    async def calc_delete(self):
        stmt = select(Calc_Model).filter(Calc_Model.id == self.event.id)
        result = await self.db.execute(stmt)
        obj = result.scalars().first()

        await self.db.delete(obj)
        await self.db.commit()

        return obj
    
    async def calc_delete_all(self):
        await self.db.execute(delete(Calc_Model))
        await self.db.commit()
        return "ok"