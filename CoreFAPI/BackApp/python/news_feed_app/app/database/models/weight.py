from uuid import UUID  # noqa: TC003

from database.models.base import Base
from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column


class AuthorWeight(Base):
    """
    Модель для хранения веса авторов в контексте персонализации пользователя.

    :ivar user_id: Идентификатор пользователя, для которого определяется вес автора.
    :ivar author_id: Идентификатор автора, чей вес определяется.
    :ivar weight: Вес автора (неотрицательное целое число).

    Ограничения:
        - Составной первичный ключ из полей user_id и author_id.
        - Проверка chk_weight_non_negative гарантирует, что weight >= 0.
    """

    __tablename__ = "author_weight"
    __table_args__ = (CheckConstraint("weight >= 0", name="chk_weight_non_negative"),)

    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    author_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    weight: Mapped[int] = mapped_column(default=0, nullable=False)


class HashtagWeight(Base):
    """
    Модель для хранения веса хештегов в контексте персонализации пользователя.

    :ivar user_id: Идентификатор пользователя, для которого определяется вес хештега.
    :ivar hashtag_id: Идентификатор хештега (внешний ключ к таблице hashtags).
    :ivar weight: Вес хештега (неотрицательное целое число).

    Ограничения:
        - Составной первичный ключ из полей user_id и hashtag_id
        - Внешний ключ на таблицу hashtags с каскадным удалением
        - Проверка chk_hashtag_weight_non_negative гарантирует weight >= 0
    """

    __tablename__ = "hashtag_weight"
    __table_args__ = (
        CheckConstraint("weight >= 0", name="chk_hashtag_weight_non_negative"),
    )

    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    hashtag_id: Mapped[int] = mapped_column(
        ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[int] = mapped_column(default=0, nullable=False)
