from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field


class PreAuthorWeightRabbit(BaseModel):
    """
    Модель события предварительного веса автора для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "pre_author_weight".
    :ivar user_id: UUID пользователя, для которого рассчитывается предварительный вес.
    :ivar post_id: Идентификатор поста, связанного с весом.
    :ivar weight: Значение предварительного веса (целое число).
    """

    type: str = Field(default="pre_author_weight")
    user_id: UUID
    post_id: int
    weight: int


class AuthorWeightRabbit(BaseModel):
    """
    Модель, представляющая вес автора для конкретного пользователя с указанием типа записи.

    :ivar type: str - Тип записи, по умолчанию "author_weight".
    :ivar user_id: UUID - UUID пользователя, для которого определяется вес автора.
    :ivar author_id: UUID - UUID автора, чей вес оценивается.
    :ivar weight: int - Добавочный вес (может быть отрицательным).
    """

    type: str = Field(default="author_weight")
    user_id: UUID
    author_id: UUID
    weight: int
