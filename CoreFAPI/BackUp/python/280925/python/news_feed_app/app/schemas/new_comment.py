from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, Field


class NewCommentRabbit(BaseModel):
    """
    Модель события нового комментария для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "new_comment".
    :ivar author_id: UUID автора поста, к которому добавлен комментарий.
    :ivar post_id: Идентификатор поста, к которому добавлен комментарий.
    :ivar comment_id: Идентификатор комментария.
    :ivar user_id: UUID пользователя, который оставил комментарий.
    """

    type: str = Field(default="new_comment")
    author_id: UUID
    post_id: int
    comment_id: int
    user_id: UUID


class PreNewCommentRabbit(BaseModel):
    """
    Модель события предварительного уведомления о новом комментарии для публикации в RabbitMQ.

    :ivar type: Тип события, по умолчанию "pre_new_comment".
    :ivar post_id: Идентификатор поста, к которому добавлен комментарий.
    :ivar comment_id: Идентификатор комментария.
    :ivar user_id: UUID пользователя, который оставил комментарий.
    """

    type: str = Field(default="pre_new_comment")
    post_id: int
    comment_id: int
    user_id: UUID
