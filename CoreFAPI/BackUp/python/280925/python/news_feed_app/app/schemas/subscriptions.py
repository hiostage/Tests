from typing import List
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict
from schemas.base import BaseSchema


class SubscriptionRead(BaseModel):
    """
    Pydantic модель для чтения данных о подписке.

    :ivar author_id: Уникальный идентификатор автора, на которого оформлена подписка.
    """

    author_id: UUID

    model_config = ConfigDict(from_attributes=True)


class OutSubscriptions(BaseSchema):
    """
    Модель ответа, содержащая список подписок и количество страниц.

    :ivar subscriptions: Список подписок пользователя.
    :ivar count_pages: Общее количество страниц с подписками (для пагинации).
    """

    subscriptions: List[SubscriptionRead]
    count_pages: int
