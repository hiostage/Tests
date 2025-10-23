from pydantic import BaseModel, EmailStr, Field

class UserScheme(BaseModel):
    name: str
    email: EmailStr = Field(example='Exampe@mail.ru')
    password: str
    phone: str


class UserSchemeID(UserScheme):
    id: int

class UserSchemeForUpdate(BaseModel):
    name : str | None = None
    email : str | None = None
    phone : str | None = None


class UserLoginSchema(BaseModel):
    name: str
    password: str


class ValueId(BaseModel):
    value_id: int

class ValueResult(BaseModel):
    id: int
    val_1: int
    val_2: int
    result: int