import re
from typing import TYPE_CHECKING, List

from database.models.base import Base
from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

if TYPE_CHECKING:
    from database.models import Posts

MAX_HASHTAG_LENGTH = 50
HASHTAG_PATTERN = re.compile(r"^#[\w\-]{1,%d}$" % (MAX_HASHTAG_LENGTH - 1))


class Hashtags(Base):
    """
    Модель для хэштегов.

    :ivar id: Уникальный идентификатор хэштега.
    :ivar name: Имя хэштега, начинающееся с #.
    :ivar created_at: Дата и время создания хэштега.
    :ivar post_hashtags: Ассоциации между хэштегом и постами.
    :ivar posts: Прокси для получения списка постов с этим хэштегом.
    """

    __tablename__ = "hashtags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(MAX_HASHTAG_LENGTH), nullable=False, unique=True, index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post_hashtags: Mapped[List["PostHashtag"]] = relationship(
        back_populates="hashtag", cascade="all, delete-orphan", passive_deletes=True
    )

    posts: AssociationProxy[List["Posts"]] = association_proxy(
        "post_hashtags", "post", creator=lambda post: PostHashtag(post=post)
    )

    @validates("name")
    def validate_hashtag(self, _key: str, value: str) -> str:
        """
        Валидация и нормализация имени хэштега.

        Выполняет:
        1. Удаление пробелов и приведение к нижнему регистру
        2. Проверку формата через регулярное выражение HASHTAG_PATTERN
        3. Детальные проверки для точного определения ошибок

        :param _key: Название атрибута (не используется)
        :param value: Входное значение для валидации
        :return: Нормализованный хэштег в нижнем регистре
        :raises ValueError: При нарушениях:
            - Пустое значение
            - Отсутствие # в начале
            - Слишком короткая/длинная длина
            - Недопустимые символы
        """
        value = value.strip().lower()

        # Одновременная проверка всех условий через regex
        if not HASHTAG_PATTERN.fullmatch(value):
            if not value:
                raise ValueError("Хэштег не может быть пустым")
            if not value.startswith("#"):
                raise ValueError("Хэштег должен начинаться с #")
            if len(value) < 2:
                raise ValueError("Хэштег должен содержать минимум 1 символ после #")
            if len(value) > MAX_HASHTAG_LENGTH:
                raise ValueError(
                    f"Максимальная длина хэштега - {MAX_HASHTAG_LENGTH} символов"
                )
            raise ValueError(
                "Хэштег может содержать только буквы, цифры, дефисы и подчёркивания"
            )
        return value

    def __repr__(self) -> str:
        """
        Возвращает строковое представление объекта хэштега.

        :return: Строка с идентификатором, именем и датой создания хэштега.
        """
        return (
            f"<Hashtag(id={self.id}, name='{self.name}', created_at={self.created_at})>"
        )


class PostHashtag(Base):
    """
    Модель для связи между постами и хэштегами.

    :ivar post_id: Идентификатор поста.
    :ivar hashtag_id: Идентификатор хэштега.
    :ivar created_at: Дата и время создания связи.
    :ivar post: Пост, с которым связан хэштег.
    :ivar hashtag: Хэштег, связанный с постом.

    Таблица имеет уникальный индекс на пару (post_id, hashtag_id) для предотвращения дубликатов.
    """

    __tablename__ = "post_hashtag"
    __table_args__ = (
        Index("ix_post_id", "post_id"),
        Index("ix_hashtag_id", "hashtag_id"),
    )

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    hashtag_id: Mapped[int] = mapped_column(
        ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post: Mapped["Posts"] = relationship(
        back_populates="post_hashtags", lazy="selectin"
    )
    hashtag: Mapped[Hashtags] = relationship(
        back_populates="post_hashtags", lazy="selectin"
    )
