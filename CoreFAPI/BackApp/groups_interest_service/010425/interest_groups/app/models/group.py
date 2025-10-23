from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

group_members = Table(
    'group_members', Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    category = Column(String(50))  # technology, programming, hobbies, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    members = relationship("User", secondary=group_members, back_populates="groups")
    posts = relationship("Post", back_populates="group")
    
    creator = relationship("User", back_populates="created_groups")