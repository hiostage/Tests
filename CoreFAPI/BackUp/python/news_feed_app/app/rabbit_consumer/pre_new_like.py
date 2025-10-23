from typing import TYPE_CHECKING, Any, Dict, Optional

from database.models import Comments, Posts
from events.utils import outer_publisher
from schemas.new_like import NewLikeRabbit, PreNewLikeRabbit
from sqlalchemy import select

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic
    from sqlalchemy.orm import Session, sessionmaker


def __pre_new_like_post(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    rabbit_model: PreNewLikeRabbit,
) -> Optional[NewLikeRabbit]:
    """
    Внутренняя функция обработки лайка к посту.

    Получает автора поста из базы данных по post_id.
    Если автор найден, формирует и возвращает модель NewLikeRabbit.
    Иначе возвращает None.

    :param app: Экземпляр приложения CustomFastApi (не используется, но может пригодиться).
    :param session_maker: Фабрика сессий SQLAlchemy.
    :param rabbit_model: Модель события PreNewLikeRabbit.
    :return: NewLikeRabbit с данными для публикации или None.
    """
    log = app.get_logger("pre_new_like_post")
    if rabbit_model.post_id is None:
        log.warning("Не указан post_id в событии: %s", rabbit_model)
        return None

    with session_maker() as session:
        author_id = session.execute(
            select(Posts.user_id).where(Posts.id == rabbit_model.post_id)
        ).scalar_one_or_none()
    if author_id is None:
        log.warning("Автор поста с id=%s не найден", rabbit_model.post_id)
        return None
    return NewLikeRabbit(
        user_id=rabbit_model.user_id,
        post_id=rabbit_model.post_id,
        author_id=author_id,
        type_object="post",
    )


def __pre_new_like_comment(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    rabbit_model: PreNewLikeRabbit,
) -> Optional[NewLikeRabbit]:
    """
    Внутренняя функция обработки лайка к комментарию.

    Получает комментарий из базы данных по comment_id.
    Если комментарий найден, формирует и возвращает модель NewLikeRabbit.
    Иначе возвращает None.

    :param app: Экземпляр приложения CustomFastApi (может быть использован при необходимости).
    :param session_maker: Фабрика сессий SQLAlchemy.
    :param rabbit_model: Модель события PreNewLikeRabbit.
    :return: NewLikeRabbit с данными для публикации или None.
    """
    log = app.get_logger("pre_new_like_comment")
    if rabbit_model.comment_id is None:
        log.warning("Не указан comment_id в событии: %s", rabbit_model)
        return None
    with session_maker() as session:
        comment = session.get(Comments, rabbit_model.comment_id)
    if comment is None:
        log.warning("Комментарий с id=%s не найден", rabbit_model.comment_id)
        return None
    return NewLikeRabbit(
        type_object="comment",
        user_id=rabbit_model.user_id,
        post_id=comment.post_id,
        author_id=comment.user_id,
        comment_id=rabbit_model.comment_id,
    )


def pre_new_like(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обработчик события предварительного уведомления о новом лайке из RabbitMQ.

    В зависимости от типа объекта ("post" или "comment") вызывает соответствующую внутреннюю функцию,
    формирует модель для публикации и отправляет её через outer_publisher.
    Подтверждает получение сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi.
    :param session_maker: Фабрика сессий SQLAlchemy для работы с БД.
    :param data: Словарь данных события, десериализуемый в PreNewLikeRabbit.
    :param method: Объект Basic.Deliver для подтверждения сообщения.
    :param ch: Канал RabbitMQ для подтверждения сообщения.
    """
    log = app.get_logger("pre_new_like")
    try:
        log.info("Получено новое сообщение: %s", data)
        rabbit_model = PreNewLikeRabbit(**data)
        if rabbit_model.type_object == "post":
            out_rabbit_model = __pre_new_like_post(app, session_maker, rabbit_model)
        elif rabbit_model.type_object == "comment":
            out_rabbit_model = __pre_new_like_comment(app, session_maker, rabbit_model)
        else:
            log.warning("Неизвестный тип объекта: %s", rabbit_model.type_object)
            return
        if out_rabbit_model is None:
            log.warning("Не удалось сформировать модель для публикации")
            return
        outer_publisher(app, out_rabbit_model)
        log.info("Сообщение опубликовано: %s", out_rabbit_model)
    finally:
        if method.delivery_tag:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log.info("Сообщение подтверждено (delivery_tag=%s)", method.delivery_tag)
