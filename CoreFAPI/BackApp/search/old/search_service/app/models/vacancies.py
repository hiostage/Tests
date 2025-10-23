from pydantic import BaseModel
from typing import List, Optional

class Vacancy(BaseModel):
    id: str
    title: str
    company: str
    skills: List[str]
    location: Optional[str] = None
    salary: Optional[int] = None
