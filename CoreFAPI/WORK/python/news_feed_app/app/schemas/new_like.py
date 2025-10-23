from typing import Optional
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field


class PreNewLikeRabbit(BaseModel):
    """
    Модель события предварительного уведомления о новом лайке для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "pre_new_like".
    :ivar type_object: Тип объекта, к которому поставлен лайк (например, "post" или "comment").
    :ivar user_id: UUID пользователя, поставившего лайк.
    :ivar post_id: Опциональный идентификатор поста, если лайк поставлен к посту.
    :ivar comment_id: Опциональный идентификатор комментария, если лайк поставлен к комментарию.
    """

    type: str = Field(default="pre_new_like")
    type_object: str
    user_id: UUID
    post_id: Optional[int] = Field(default=None)
    comment_id: Optional[int] = Field(default=None)


class NewLikeRabbit(BaseModel):
    """
    Модель события уведомления о новом лайке для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "new_like".
    :ivar type_object: Тип объекта, к которому поставлен лайк (например, "post" или "comment").
    :ivar user_id: UUID пользователя, поставившего лайк.
    :ivar post_id: Идентификатор поста, которому поставлен лайк.
    :ivar author_id: UUID автора поста.
    :ivar comment_id: Опциональный идентификатор комментария, если лайк поставлен к комментарию.
    """

    type: str = Field(default="new_like")
    type_object: str
    user_id: UUID
    post_id: int
    author_id: UUID
    comment_id: Optional[int] = Field(default=None)
