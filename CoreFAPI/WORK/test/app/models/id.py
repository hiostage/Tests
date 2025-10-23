from sqlalchemy import Column, Integer, String 
from app.db.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class Iddd(Base):
    __tablename__ = "Iddd"

    id = Column(Integer, primary_key=True)
    name = Column(String)
