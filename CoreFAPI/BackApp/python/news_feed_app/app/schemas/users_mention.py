from typing import List, Optional

from pydantic import BaseModel, Field


class UsersMention(BaseModel):
    """
    Модель данных для хранения информации об упоминаниях пользователей.

    :ivar type: Тип объекта, по умолчанию "mentioning_users".
    :ivar type_mention: Тип упоминания (например, 'post', 'comment').
    :ivar event_mention: Событие, связанное с упоминанием (например, 'insert', 'update').
    :ivar usernames: Список имен пользователей, упомянутых в тексте.
    :ivar post_id: Идентификатор поста, в котором обнаружено упоминание.
    :ivar comment_id: Идентификатор комментария, в котором обнаружено упоминание (если применимо).
    """

    type: str = Field(default="mentioning_users")
    type_mention: str
    event_mention: str
    usernames: List[str]
    post_id: int
    comment_id: Optional[int] = None
