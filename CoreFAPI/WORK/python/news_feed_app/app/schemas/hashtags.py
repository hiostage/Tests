from pydantic import BaseModel, ConfigDict


class OutHashtags(BaseModel):
    """
    Схема ответа для хэштегов.

    :ivar name: Название хэштега
    """

    name: str

    model_config = ConfigDict(from_attributes=True)
