from typing import TYPE_CHECKING, Any, Dict

from database.models import Posts
from events.utils import outer_publisher
from schemas.new_comment import NewCommentRabbit, PreNewCommentRabbit
from sqlalchemy import select

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic
    from sqlalchemy.orm import Session, sessionmaker


def pre_new_comment(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обрабатывает событие предварительного уведомления о новом комментарии из RabbitMQ.

    Извлекает автора поста по post_id из базы данных.
    Если автор найден, создаёт и отправляет событие NewCommentRabbit.
    Если автор не найден, логирует предупреждение.
    Подтверждает обработку сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi для логирования и публикации.
    :param session_maker: Фабрика сессий SQLAlchemy для работы с БД.
    :param data: Словарь с данными события (должен соответствовать PreNewCommentRabbit).
    :param method: Объект Basic.Deliver для подтверждения сообщения.
    :param ch: Канал RabbitMQ для подтверждения сообщения.
    """
    try:
        log = app.get_logger("pre_new_comment")
        rabbit_model = PreNewCommentRabbit(**data)
        with session_maker() as session:
            author_id = session.execute(
                select(Posts.user_id).where(Posts.id == rabbit_model.post_id)
            ).scalar_one_or_none()
        if author_id:
            out_rabbit_model = NewCommentRabbit(
                author_id=author_id,
                post_id=rabbit_model.post_id,
                comment_id=rabbit_model.comment_id,
                user_id=rabbit_model.user_id,
            )
            outer_publisher(app, out_rabbit_model)
            log.info(
                "Отправлено событие NewCommentRabbit: user_id=%s, author_id=%s, post_id=%s, comment_id=%s",
                rabbit_model.user_id,
                author_id,
                rabbit_model.post_id,
                rabbit_model.comment_id,
            )
        else:
            log.warning(
                "Не удалось найти автора поста с ID %s. Событие NewCommentRabbit не отправлено.",
                rabbit_model.post_id,
            )
    finally:
        if method.delivery_tag:
            ch.basic_ack(delivery_tag=method.delivery_tag)
