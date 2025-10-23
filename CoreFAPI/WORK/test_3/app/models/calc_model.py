from sqlalchemy import Column, Integer
from app.database.database import Base

class Calc_Model(Base):
    __tablename__ = 'Goodnes'

    id = Column(Integer, primary_key = True)
    val_1 = Column(Integer)
    val_2 = Column(Integer)
    result = Column(Integer)