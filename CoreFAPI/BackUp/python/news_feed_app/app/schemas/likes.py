from typing import List
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict
from schemas.base import BaseSchema


class UserAddedLikeRead(BaseModel):
    """
    Схема для возвращения user_id при наличии его лайка.
    """

    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class OutLikes(BaseSchema):
    """
    Схема ответа с коллекцией лайков и информацией о количестве страниц.

    :ivar likes: Список лайков с данными пользователей.
    :ivar count_pages: Общее количество страниц с лайками.
    """

    likes: List[UserAddedLikeRead]
    count_pages: int
