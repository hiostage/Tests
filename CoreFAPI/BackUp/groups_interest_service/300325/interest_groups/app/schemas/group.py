from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    created_at: datetime
    creator_id: int
    
    class Config:
        orm_mode = True

class GroupWithMembers(Group):
    members: List[int]