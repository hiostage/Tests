from sqlalchemy import Column, Integer, String
from app.db.database import Base

class Sum(Base):
    __tablename__="SUMM"

    id = Column(Integer, primary_key=True)
    a = Column(Integer)
    b = Column(Integer)
    result= Column(Integer)
    