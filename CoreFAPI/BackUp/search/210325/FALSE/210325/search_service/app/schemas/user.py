from pydantic import BaseModel
from typing import Optional, List

class User(BaseModel):
    id: int
    name: str
    skills: List[str]
    location: str

class UserSearchRequest(BaseModel):
    query: Optional[str] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None