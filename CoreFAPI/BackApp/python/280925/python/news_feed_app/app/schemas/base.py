from pydantic import BaseModel


class BaseSchema(BaseModel):
    """
    Базовая схема для ответов API.

    :ivar result: Результат операции
    """

    result: bool = True
