from typing import TYPE_CHECKING, Any, Dict

from database.models import AuthorWeight, Posts
from events.utils import inner_publisher
from schemas.author_weight import AuthorWeightRabbit, PreAuthorWeightRabbit
from sqlalchemy import select

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic
    from sqlalchemy.orm import Session, sessionmaker


def update_or_create_author_weight(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обновляет существующую запись веса автора для пользователя или создаёт новую.

    Функция пытается найти запись в базе по author_id и user_id.
    Если запись найдена, обновляет поле weight, не позволяя уйти в отрицательное значение.
    Если записи нет - создаёт новую с весом не меньше нуля.
    Логирует операции и подтверждает получение сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi для логирования и доступа к БД.
    :param session_maker: Фабрика сессий SQLAlchemy.
    :param data: Словарь с данными для создания AuthorWeightRabbit.
    :param method: Объект Basic.Deliver с информацией о доставке сообщения RabbitMQ.
    :param ch: Канал RabbitMQ для подтверждения доставки.
    """
    log = app.get_logger("update_or_create_author_weight")
    log.info("Получено сообщение из RabbitMQ: %s", data)
    author_weight = AuthorWeightRabbit(**data)

    with session_maker() as session:
        weight_in_bd = (
            session.execute(
                select(AuthorWeight).where(
                    AuthorWeight.author_id == author_weight.author_id,
                    AuthorWeight.user_id == author_weight.user_id,
                )
            )
            .scalars()
            .one_or_none()
        )
        if weight_in_bd is None:
            weight_in_bd = AuthorWeight(
                author_id=author_weight.author_id,
                user_id=author_weight.user_id,
                weight=author_weight.weight if author_weight.weight > 0 else 0,
            )
            session.add(weight_in_bd)
            log.info(
                "Создан новый вес: author_id=%s, user_id=%s, weight=%s",
                weight_in_bd.author_id,
                weight_in_bd.user_id,
                weight_in_bd.weight,
            )
        else:
            old = weight_in_bd.weight
            weight_in_bd.weight = max(0, weight_in_bd.weight + author_weight.weight)
            log.info(
                "Обновлён вес: author_id=%s, user_id=%s, old=%s, delta=%s, new=%s",
                author_weight.author_id,
                author_weight.user_id,
                old,
                author_weight.weight,
                weight_in_bd.weight,
            )

        session.commit()

    if method.delivery_tag:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def pre_update_or_create_author_weight(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обрабатывает событие предварительного веса автора из RabbitMQ.

    Извлекает автора поста по post_id из базы данных и, если найден,
    создаёт и отправляет событие AuthorWeightRabbit с весом.
    Если пост не найден, логирует предупреждение.
    Подтверждает обработку сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi для логирования и публикации.
    :param session_maker: Фабрика сессий SQLAlchemy для работы с БД.
    :param data: Словарь с данными события (должен соответствовать PreAuthorWeightRabbit).
    :param method: Объект Basic.Deliver для подтверждения сообщения.
    :param ch: Канал RabbitMQ для подтверждения сообщения.
    """
    try:
        log = app.get_logger("pre_update_or_create_author_weight")
        rabbit_model = PreAuthorWeightRabbit(**data)
        with session_maker() as session:
            author_id = session.execute(
                select(Posts.user_id).where(Posts.id == rabbit_model.post_id)
            ).scalar_one_or_none()
        if author_id:
            out_rabbit_model = AuthorWeightRabbit(
                user_id=rabbit_model.user_id,
                author_id=author_id,
                weight=rabbit_model.weight,
            )
            inner_publisher(app, out_rabbit_model)
            log.info(
                "Отправлено сообщение AuthorWeightRabbit: user_id=%s, author_id=%s, weight=%s",
                rabbit_model.user_id,
                author_id,
                rabbit_model.weight,
            )
        else:
            log.warning(
                "Пост с ID %s не найден. Сообщение пропущено.", rabbit_model.post_id
            )
    finally:
        if method.delivery_tag:
            ch.basic_ack(delivery_tag=method.delivery_tag)
