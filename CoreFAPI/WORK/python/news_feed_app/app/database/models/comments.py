from typing import TYPE_CHECKING, List
from uuid import UUID  # noqa: TC003

from database.models.base import Base
from database.models.likes import Likes
from sqlalchemy import DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.orm import (
    Mapped,
    column_property,
    mapped_column,
    relationship,
    validates,
)

MAX_COMMENT_LENGTH = 5000


if TYPE_CHECKING:
    from database.models import Posts


class Comments(Base):
    """
    ORM-модель для представления комментариев к постам/новостям.

    :ivar id: Уникальный идентификатор комментария.
    :ivar user_id: Идентификатор пользователя, оставившего комментарий.
    :ivar post_id: Идентификатор поста, к которому относится комментарий.
    :ivar comment: Текст комментария (максимальная длина - MAX_COMMENT_LENGTH).
    :ivar created_at: Время создания комментария (автоматически заполняется).
    :ivar updated_at: Время последнего обновления комментария (автоматически обновляется).
    :ivar post: Связь с родительским постом (relationship back_populates).

    Примечания:
        - При удалении поста (posts.id) все связанные комментарии каскадно удаляются.
        - Поле created_at инициализируется временем создания записи в БД.
        - Поле updated_at автоматически обновляется при изменении записи.
    """

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), nullable=False)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    comment: Mapped[str] = mapped_column(String(MAX_COMMENT_LENGTH), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    post: Mapped["Posts"] = relationship(back_populates="comments")
    likes: Mapped[List[Likes]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )
    likes_count = column_property(
        select(func.count(Likes.id))
        .where(Likes.comment_id == id)
        .correlate_except(Likes)
        .scalar_subquery()
    )

    @validates("comment")
    def validate_comment(self, _: str, value: str) -> str:
        """
        Проверяет валидность комментария перед сохранением в БД.

        Проверки:
        - Длина комментария не превышает MAX_COMMENT_LENGTH символов.

        :raises ValueError: Если длина комментария превышает максимально допустимую.
        :param _: Название поля (не используется).
        :param value: Проверяемое значение комментария.
        :return: Оригинальное значение при успешной проверке.
        """

        if len(value) > MAX_COMMENT_LENGTH:
            raise ValueError(
                f"Комментарий должен быть <= {MAX_COMMENT_LENGTH} символов."
            )
        return value
