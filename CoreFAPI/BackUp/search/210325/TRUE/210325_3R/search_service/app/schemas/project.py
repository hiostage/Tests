from pydantic import BaseModel
from typing import Optional, List

class Project(BaseModel):
    id: int
    name: str
    description: str
    technologies: List[str]

class ProjectSearchRequest(BaseModel):
    query: Optional[str] = None
    technologies: Optional[List[str]] = None