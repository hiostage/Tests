from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: str
    first_name: str
    last_name: str
    skills: List[str]
    location: Optional[str] = None
    company: Optional[str] = None
