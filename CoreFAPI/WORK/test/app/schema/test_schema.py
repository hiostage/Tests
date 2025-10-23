from pydantic import BaseModel

class Test_schema(BaseModel):
    id: int
    name: str