from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    
    groups = relationship("Group", secondary="group_members", back_populates="members")
    posts = relationship("Post", back_populates="author")
    created_groups = relationship("Group", back_populates="creator")