from sqlalchemy import Column, Integer, String

from app.database.database import Base

class User(Base):
    __tablename__ = "USERS"


    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    password = Column(String(), nullable=False)
    email = Column(String(64), nullable=False)
    phone = Column(String(13), nullable=False)
    value_result = Column(String())