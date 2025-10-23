from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field


class NewSubscriberRabbit(BaseModel):
    """
    Модель данных для события нового подписчика.

    :ivar type: Тип события, по умолчанию "new_subscriber".
    :ivar author_id: Уникальный идентификатор автора, на которого подписываются.
    :ivar subscriber_id: Уникальный идентификатор пользователя, который подписался.
    """

    type: str = Field(default="new_subscriber")
    author_id: UUID
    subscriber_id: UUID
