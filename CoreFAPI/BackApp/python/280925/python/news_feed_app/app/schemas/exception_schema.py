from pydantic import BaseModel


class ErrorSchema(BaseModel):
    """
    Схема при ошибке.
    """

    result: bool = False
    error_type: str
    error_message: str
