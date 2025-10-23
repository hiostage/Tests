from typing import TYPE_CHECKING, Optional
from uuid import UUID  # noqa: TC003

from database.models.base import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

if TYPE_CHECKING:
    from database.models import Comments, Posts


class Likes(Base):
    """
    Модель лайков для постов и комментариев с взаимным исключением.

    :ivar id: Уникальный идентификатор лайка
    :ivar user_id: UUID пользователя, поставившего лайк
    :ivar post_id: ID поста (обязательно, если comment_id не задан)
    :ivar comment_id: ID комментария (обязательно, если post_id не задан)
    :ivar created_at: Дата создания записи (автоматически)
    :ivar post: Связь с постом (отношение многие-к-одному)
    :ivar comment: Связь с комментарием (отношение многие-к-одному)

    **Ограничения:**
    - Одно целевое поле: post_id ИЛИ comment_id (CheckConstraint)
    - Уникальность: Один лайк от пользователя на пост/комментарий
    """

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), nullable=False)
    post_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        server_default=None,
    )
    comment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        server_default=None,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    post: Mapped[Optional["Posts"]] = relationship(back_populates="likes")
    comment: Mapped[Optional["Comments"]] = relationship(back_populates="likes")

    __table_args__ = (
        CheckConstraint(
            "(post_id IS NULL) != (comment_id IS NULL)", name="only_one_target"
        ),
        Index(
            "uq_likes_user_post",
            "user_id",
            "post_id",
            unique=True,
            postgresql_where=text("comment_id IS NULL"),
        ),
        Index(
            "uq_likes_user_comment",
            "user_id",
            "comment_id",
            unique=True,
            postgresql_where=text("post_id IS NULL"),
        ),
    )

    @validates("post_id")
    def validate_post_id(self, _: str, value: int | None) -> int | None:
        """
        Проверка существования comment_id, если задаётся post_id
        """
        if self.comment_id is not None:
            raise ValueError("Уже задан comment_id.")
        return value

    @validates("comment_id")
    def validate_comment_id(self, _: str, value: int | None) -> int | None:
        """
        Проверка существования post_id, если задаётся comment_id
        """
        if self.post_id is not None:
            raise ValueError("Уже задан post_id.")
        return value
