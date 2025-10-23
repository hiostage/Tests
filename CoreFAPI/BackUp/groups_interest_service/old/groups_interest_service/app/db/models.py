from sqlalchemy import Column, Integer, String, Boolean, Text, ARRAY, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String))
    creator_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default="now()")
    is_private = Column(Boolean, default=False)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    author_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default="now()")