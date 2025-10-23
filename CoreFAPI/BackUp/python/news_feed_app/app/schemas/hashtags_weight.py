from typing import Sequence
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field


class PreHashtagsWeightRabbit(BaseModel):
    """
    Модель события предварительного веса хештегов для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "pre_hashtags_weight".
    :ivar user_id: UUID пользователя, для которого рассчитывается предварительный вес.
    :ivar post_id: Идентификатор поста, связанного с весом.
    :ivar weight: Значение предварительного веса (целое число).
    """

    type: str = Field(default="pre_hashtags_weight")
    user_id: UUID
    post_id: int
    weight: int


class HashtagsWeightRabbit(BaseModel):
    """
    Модель, представляющая вес хэштегов для конкретного пользователя с указанием типа записи.

    :ivar type: str - Тип записи, по умолчанию "hashtags_weight".
    :ivar user_id: UUID - UUID пользователя, для которого определяется вес хэштегов.
    :ivar hashtags_ids: Sequence[int] - Последовательность идентификаторов хэштегов.
    :ivar weight: int - Добавочный вес (может быть отрицательным).
    """

    type: str = Field(default="hashtags_weight")
    user_id: UUID
    hashtags_ids: Sequence[int]
    weight: int
