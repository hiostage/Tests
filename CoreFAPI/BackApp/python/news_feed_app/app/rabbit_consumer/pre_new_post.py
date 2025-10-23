from typing import TYPE_CHECKING, Any, Dict, Sequence

from database.models import Subscriptions
from events.utils import outer_publisher
from schemas.new_post import NewPostRabbit, PreNewPostRabbit
from sqlalchemy import select

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic
    from sqlalchemy.orm import Session, sessionmaker


def pre_new_post(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обрабатывает событие предварительного уведомления о новом посте из RabbitMQ.

    Извлекает подписчиков автора из базы данных.
    Если подписчики найдены, формирует и отправляет событие NewPostRabbit.
    Если подписчиков нет - логирует информацию.
    Подтверждает обработку сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi для логирования и публикации.
    :param session_maker: Фабрика сессий SQLAlchemy для работы с БД.
    :param data: Словарь с данными события (должен соответствовать PreNewPostRabbit).
    :param method: Объект Basic.Deliver для подтверждения сообщения.
    :param ch: Канал RabbitMQ для подтверждения сообщения.
    """
    try:
        log = app.get_logger("pre_new_post")
        rabbit_model = PreNewPostRabbit(**data)
        with session_maker() as session:
            subscribers: Sequence[Subscriptions] = (
                session.execute(
                    select(Subscriptions).where(
                        Subscriptions.author_id == rabbit_model.author_id
                    )
                )
                .scalars()
                .all()
            )
        if subscribers:
            subscribers_ids = [subscriber.user_id for subscriber in subscribers]
            log.info(
                "Найдено %d подписчиков у автора %s. Отправляем событие.",
                len(subscribers_ids),
                str(rabbit_model.author_id),
            )
            out_rabbit_model = NewPostRabbit(
                post_id=rabbit_model.post_id,
                author_id=rabbit_model.author_id,
                subscribers_ids=subscribers_ids,
            )
            outer_publisher(app, out_rabbit_model)
        else:
            log.info(
                "У автора %s нет подписчиков, сообщение не отправлено",
                str(rabbit_model.author_id),
            )
    finally:
        if method.delivery_tag:
            ch.basic_ack(delivery_tag=method.delivery_tag)
