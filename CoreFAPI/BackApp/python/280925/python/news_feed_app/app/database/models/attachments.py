from typing import Optional
from uuid import UUID  # noqa: TC003

from database.models.base import Base
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    validates,
)

MAX_CAPTION_LENGTH = 2000


class Attachments(Base):
    """
    Модель "Вложения".

    :ivar id: ID вложения
    :ivar post_id: ID новости (может быть None)
    :ivar user_id: ID пользователя
    :ivar attachment_path: Путь к вложению
    :ivar post: Связанная новость (модель Posts)
    :ivar created_at: Дата и время создания вложения
    :ivar is_deleted: Флаг мягкого удаления (True = удалено)
    """

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(column="posts.id", ondelete="SET NULL"), nullable=True, default=None
    )
    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), nullable=False)
    attachment_path: Mapped[str] = mapped_column(String, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(
        String(MAX_CAPTION_LENGTH), nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    @validates("caption")
    def validate_caption(self, _: str, value: str) -> str | None:
        """
        Валидация описания вложения.

        Проверяет, что длина описания не превышает MAX_CAPTION_LENGTH символов,
        если описание не None.

        :param _: Неиспользуемый параметр.
        :param value: Значение описания.
        :return: Валидированное значение описания.
        :raises ValueError: Если длина описания превышает MAX_CAPTION_LENGTH.
        """
        if value is not None and len(value) > MAX_CAPTION_LENGTH:
            raise ValueError(
                f"Описание вложения должно быть <= {MAX_CAPTION_LENGTH} символов."
            )
        return value
