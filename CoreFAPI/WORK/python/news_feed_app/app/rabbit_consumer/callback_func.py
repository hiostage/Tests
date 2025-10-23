import json
from typing import TYPE_CHECKING

from rabbit_consumer.author_weight import (
    pre_update_or_create_author_weight,
    update_or_create_author_weight,
)
from rabbit_consumer.hashtags_weight import (
    pre_update_or_create_hashtag_weight,
    update_or_create_hashtag_weight,
)
from rabbit_consumer.pre_new_comment import pre_new_comment
from rabbit_consumer.pre_new_like import pre_new_like
from rabbit_consumer.pre_new_post import pre_new_post

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.spec import Basic, BasicProperties


def callback_func(
    ch: "BlockingChannel",
    method: "Basic.Deliver",
    properties: "BasicProperties",
    body: bytes,
    my_app: "CustomFastApi",
) -> None:
    """
    Callback-функция для обработки сообщений из RabbitMQ.

    В зависимости от типа сообщения вызывает соответствующую функцию обработки.

    :param ch: Канал RabbitMQ.
    :param method: Информация о доставке сообщения.
    :param properties: Свойства сообщения.
    :param body: Тело сообщения в байтах.
    :param my_app: Экземпляр приложения CustomFastApi.
    """
    session_maker = my_app.get_sync_db().get_sync_session_fabric()
    data = json.loads(body)
    args = my_app, session_maker, data, method, ch
    match data["type"]:
        case "author_weight":
            update_or_create_author_weight(*args)
        case "hashtags_weight":
            update_or_create_hashtag_weight(*args)
        case "pre_author_weight":
            pre_update_or_create_author_weight(*args)
        case "pre_hashtags_weight":
            pre_update_or_create_hashtag_weight(*args)
        case "pre_new_comment":
            pre_new_comment(*args)
        case "pre_new_post":
            pre_new_post(*args)
        case "pre_new_like":
            pre_new_like(*args)
