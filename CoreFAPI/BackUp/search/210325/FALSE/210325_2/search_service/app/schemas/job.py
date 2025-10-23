from pydantic import BaseModel
from typing import Optional, List

class Job(BaseModel):
    id: int
    title: str
    company: str
    skills: List[str]
    location: str
    salary: float

class JobSearchRequest(BaseModel):
    query: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None