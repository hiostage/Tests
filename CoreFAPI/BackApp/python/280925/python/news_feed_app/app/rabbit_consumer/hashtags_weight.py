from typing import TYPE_CHECKING, Any, Dict, Sequence

from database.models import HashtagWeight
from database.models.hashtags import PostHashtag
from events.utils import inner_publisher
from schemas.hashtags_weight import HashtagsWeightRabbit, PreHashtagsWeightRabbit
from sqlalchemy import select

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic
    from sqlalchemy.orm import Session, sessionmaker


def update_or_create_hashtag_weight(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обновляет или создаёт записи веса хэштегов для пользователя.

    Для каждого хэштега из списка функция проверяет наличие записи в базе.
    Если запись существует, обновляет вес, не позволяя ему стать отрицательным.
    Если записи нет - создаёт новую с весом не меньше нуля.
    Логирует процесс и подтверждает получение сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi для логирования и доступа к БД.
    :param session_maker: Фабрика сессий SQLAlchemy.
    :param data: Словарь с данными для создания HashtagsWeightRabbit.
    :param method: Объект Basic.Deliver с информацией о доставке сообщения RabbitMQ.
    :param ch: Канал RabbitMQ для подтверждения доставки.
    """
    log = app.get_logger("update_or_create_hashtag_weight")
    log.info("Получено сообщение от RabbitMQ: %s", data)
    hashtags_weight = HashtagsWeightRabbit(**data)
    with session_maker() as session:
        hashtags_weight_in_bd = (
            session.execute(
                select(HashtagWeight).where(
                    HashtagWeight.user_id == hashtags_weight.user_id,
                    HashtagWeight.hashtag_id.in_(hashtags_weight.hashtags_ids),
                )
            )
            .scalars()
            .all()
        )
        existing = {hw.hashtag_id: hw for hw in hashtags_weight_in_bd}

        for hashtag_id in hashtags_weight.hashtags_ids:
            if hashtag_id in existing:
                old_weight = existing[hashtag_id].weight
                new_weight = max(0, old_weight + hashtags_weight.weight)
                existing[hashtag_id].weight = new_weight
                log.info(
                    "Обновлён вес хэштега: hashtag_id=%s, old=%s, delta=%s, new=%s",
                    hashtag_id,
                    old_weight,
                    hashtags_weight.weight,
                    new_weight,
                )
            else:
                new_weight = max(0, hashtags_weight.weight)
                session.add(
                    HashtagWeight(
                        user_id=hashtags_weight.user_id,
                        hashtag_id=hashtag_id,
                        weight=new_weight,
                    )
                )
                log.info(
                    "Создан новый вес хэштега: hashtag_id=%s, user_id=%s, weight=%s",
                    hashtag_id,
                    hashtags_weight.user_id,
                    new_weight,
                )

        session.commit()

    if method.delivery_tag:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def pre_update_or_create_hashtag_weight(
    app: "CustomFastApi",
    session_maker: "sessionmaker[Session]",
    data: Dict[str, Any],
    method: "Basic.Deliver",
    ch: "BlockingChannel",
) -> None:
    """
    Обрабатывает событие предварительного веса хештегов из RabbitMQ.

    Извлекает все хештеги, связанные с постом по post_id из базы данных.
    Если хештеги найдены, создаёт и отправляет событие HashtagsWeightRabbit с весом.
    Если хештегов нет, логирует информацию.
    Подтверждает обработку сообщения в RabbitMQ.

    :param app: Экземпляр приложения CustomFastApi для логирования и публикации.
    :param session_maker: Фабрика сессий SQLAlchemy для работы с БД.
    :param data: Словарь с данными события (должен соответствовать PreHashtagsWeightRabbit).
    :param method: Объект Basic.Deliver для подтверждения сообщения.
    :param ch: Канал RabbitMQ для подтверждения сообщения.
    """
    try:
        log = app.get_logger("pre_update_or_create_hashtag_weight")
        rabbit_model = PreHashtagsWeightRabbit(**data)
        with session_maker() as session:
            posts_hashtags: Sequence[PostHashtag] = (
                session.execute(
                    select(PostHashtag).where(
                        PostHashtag.post_id == rabbit_model.post_id
                    )
                )
                .scalars()
                .all()
            )
        if posts_hashtags:
            hashtags_ids = [post_hashtag.hashtag_id for post_hashtag in posts_hashtags]
            out_model = HashtagsWeightRabbit(
                user_id=rabbit_model.user_id,
                hashtags_ids=hashtags_ids,
                weight=rabbit_model.weight,
            )
            inner_publisher(app, out_model)
            log.info(
                "Опубликовано сообщение HashtagsWeightRabbit: user_id=%s, hashtags=%s, weight=%s",
                rabbit_model.user_id,
                hashtags_ids,
                rabbit_model.weight,
            )
        else:
            log.info(
                "Для поста с ID %s не найдено хэштегов. Сообщение не опубликовано.",
                rabbit_model.post_id,
            )
    finally:
        if method.delivery_tag:
            ch.basic_ack(delivery_tag=method.delivery_tag)
