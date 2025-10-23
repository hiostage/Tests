from uuid import UUID  # noqa: TC003

from database.models.base import Base
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Subscriptions(Base):
    """
    Модель подписки пользователя на автора.

    :ivar user_id: UUID пользователя, который подписывается (первичный ключ).
    :ivar author_id: UUID автора, на которого подписываются (первичный ключ).
    :ivar created_at: Дата и время создания подписки.
    """

    __tablename__ = "subscriptions"

    user_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)
    author_id: Mapped[UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
