from pydantic import BaseModel
from typing import Optional, List

class SearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Optional[dict] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"