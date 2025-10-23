from pydantic import BaseModel


class Proba(BaseModel):
    a: int
    b: int


class Calc(BaseModel):
    a: int
    b: int
    result: int | None = None

class Calc_with_id(BaseModel):
    id: int
    a: int
    b: int
    result: int | None = None