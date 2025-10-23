from pydantic import BaseModel

class calc_Scheme(BaseModel):
    val_1: int
    val_2: int


class Calc_Upgrade(calc_Scheme):
    id:int

class calc_Result(calc_Scheme):
    result: int

class calc_With_ID(calc_Result):
    id: int


class Calc_Scheme_Delete(BaseModel):
    id: int