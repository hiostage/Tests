from datetime import datetime  # noqa: TC003
from typing import List
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field
from schemas.base import BaseSchema

MAX_COMMENT_LENGTH = 5000


class CommentRead(BaseSchema):
    """
    Схема для чтения комментариев.

    :ivar id: Уникальный идентификатор комментария.
    :ivar user_id: Идентификатор пользователя, оставившего комментарий.
    :ivar post_id: Идентификатор поста, к которому относится комментарий.
    :ivar comment: Текст комментария.
    :ivar created_at: Дата и время создания комментария.
    :ivar updated_at: Дата и время последнего обновления комментария.
    :ivar likes_count: Количество лайков у комментария.
    :ivar is_liked_by_me: Признак, поставил ли текущий пользователь лайк (по умолчанию False).
    """

    id: int
    user_id: UUID
    post_id: int
    comment: str
    created_at: datetime
    updated_at: datetime
    likes_count: int
    is_liked_by_me: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)


class ShortCommentRead(BaseModel):
    """
    Краткий вывод коментария

    :ivar id Индетификатор коментария
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


class OutComment(BaseSchema):
    """
    Полная схема вывода коментария.

    :ivar result: Результат операции
    :ivar comment: Детальная информация о коментарии
    """

    comment: CommentRead


class OutComments(BaseSchema):
    """
    Схема ответа с коллекцией комментариев и информацией о количестве страниц.

    :ivar comments: Список комментариев.
    :ivar count_pages: Общее количество страниц с комментариями.
    """

    comments: List[CommentRead]
    count_pages: int


class ShortOutComment(BaseSchema):
    """
    Краткая схема вывода коментария.

    :ivar result: Результат операции
    :ivar post: Краткая информация о коментарии
    """

    comment: ShortCommentRead


class CommentCreate(BaseModel):
    """
    Модель для создания комментария

    :ivar comment: Содержимое комментария
    :raise HTTPException: 422 при длине комментария <1 и более MAX_COMMENT_LENGTH
    """

    comment: str = Field(min_length=1, max_length=MAX_COMMENT_LENGTH)
