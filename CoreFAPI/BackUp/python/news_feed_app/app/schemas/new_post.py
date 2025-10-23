from typing import List
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field


class PreNewPostRabbit(BaseModel):
    """
    Модель события предварительного уведомления о новом посте для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "pre_new_post".
    :ivar post_id: Идентификатор поста.
    :ivar author_id: UUID автора поста.
    """

    type: str = Field(default="pre_new_post")
    post_id: int
    author_id: UUID


class NewPostRabbit(BaseModel):
    """
    Модель события уведомления о новом посте для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "new_post".
    :ivar post_id: Идентификатор поста.
    :ivar author_id: UUID автора поста.
    :ivar subscribers_ids: Список UUID подписчиков автора, которым отправляется уведомление.
    """

    type: str = Field(default="new_post")
    post_id: int
    author_id: UUID
    subscribers_ids: List[UUID]
