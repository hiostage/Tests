from typing import TYPE_CHECKING, List, Optional
from uuid import UUID  # noqa: TC003

from database.models.base import Base
from database.models.comments import Comments
from database.models.hashtags import PostHashtag
from database.models.likes import Likes
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import (
    Mapped,
    aliased,
    column_property,
    mapped_column,
    relationship,
    validates,
)

if TYPE_CHECKING:

    from database.models.attachments import Attachments
    from database.models.hashtags import Hashtags


MAX_TITLE_LENGTH = 255
MAX_CONTENT_LENGTH = 20000


class Posts(Base):
    """
    Модель постов/новостей с поддержкой репостов и медиавложений.

    :ivar id: Уникальный идентификатор поста (первичный ключ)
    :ivar user_id: UUID автора поста
    :ivar title: Заголовок поста (до MAX_TITLE_LENGTH символов)
    :ivar content: Содержимое поста (до MAX_CONTENT_LENGTH символов)
    :ivar created_at: Дата создания записи (автоматически)
    :ivar updated_at: Дата обновления записи (автоматически)
    :ivar original_post_id: ID оригинального поста для репостов
    :ivar original_post: Ссылка на оригинальный пост (self-relationship)
    :ivar likes_count: Количество лайков (вычисляемое поле)
    :ivar comments_count: Количество комментариев (вычисляемое поле)
    :ivar reposts_count: Количество репостов (вычисляемое поле)
    :ivar attachments: Список медиавложений (отношение 1-ко-многим)
    :ivar likes: Список лайков (каскадное удаление)
    :ivar post_hashtags: Связь с хэштегами через ассоциативную таблицу
    :ivar hashtags: Прокси для доступа к хэштегам (association_proxy)
    :ivar comments: Список комментариев (каскадное удаление)
    """

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(
        String(MAX_TITLE_LENGTH), nullable=True, default=None, server_default=None
    )
    content: Mapped[Optional[str]] = mapped_column(
        String(MAX_CONTENT_LENGTH), nullable=True, default=None, server_default=None
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    original_post_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
    )

    original_post: Mapped[Optional["Posts"]] = relationship(
        foreign_keys=[original_post_id], remote_side=[id]
    )

    likes_count = column_property(
        select(func.count(Likes.id))
        .where(Likes.post_id == id)
        .correlate_except(Likes)
        .scalar_subquery()
    )

    comments_count = column_property(
        select(func.count(Comments.id))
        .where(Comments.post_id == id)
        .correlate_except(Comments)
        .scalar_subquery()
    )

    @classmethod
    def __declare_last__(cls) -> None:
        post_alias = aliased(cls)
        cls._reposts_count = column_property(
            select(func.count(post_alias.id))
            .where(post_alias.original_post_id == cls.id)
            .correlate_except(post_alias)
            .scalar_subquery()
        )

    @property
    def reposts_count(self) -> int:
        """
        Возвращает значение _reposts_count
        """
        value = self._reposts_count  # type: ignore
        if not isinstance(value, int):
            raise ValueError("Внезапно reposts_count не int")
        return value

    attachments: Mapped[List["Attachments"]] = relationship(lazy="selectin")
    likes: Mapped[List[Likes]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    post_hashtags: Mapped[List[PostHashtag]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    hashtags: AssociationProxy[List["Hashtags"]] = association_proxy(
        "post_hashtags", "hashtag", creator=lambda hashtag: PostHashtag(hashtag=hashtag)
    )

    comments: Mapped[List["Comments"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )

    @validates("content")
    def validate_content(self, _: str, value: str | None) -> str | None:
        """Валидация длины контента новости.

        :param _: Название атрибута (не используется)
        :param value: Проверяемый текст контента
        :return: Валидный текст без изменений
        :raises ValueError: Если длина превышает MAX_CONTENT_LENGTH
        """
        if value is None:
            return value
        if len(value) > MAX_CONTENT_LENGTH:
            raise ValueError(f"Новость должна быть <= {MAX_CONTENT_LENGTH} символов.")
        return value

    @validates("title")
    def validate_title(self, _: str, value: str) -> str | None:
        """Валидация длины заголовка новости.

        :param _: Название атрибута (не используется)
        :param value: Проверяемый текст заголовка
        :return: Валидный текст без изменений
        :raises ValueError: Если длина превышает MAX_TITLE_LENGTH
        """
        if value is None:
            return value
        if len(value) > MAX_TITLE_LENGTH:
            raise ValueError(
                f"Заголовок новости должен быть <= {MAX_TITLE_LENGTH} символов."
            )
        return value
