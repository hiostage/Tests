import re
from typing import TYPE_CHECKING, Any, Callable, Optional

from pika import BasicProperties
from pika.exceptions import AMQPError
from schemas.users_mention import UsersMention

if TYPE_CHECKING:
    from logging import Logger

    from app_utils.rabbitmq_manager import RabbitMQClient
    from core.classes.app import CustomFastApi


MENTION_REGEX = re.compile(r"@(\w{3,32})")


def search_for_users_mention(
    type_mention: str,
    event_mention: str,
    text: Optional[str],
    post_id: int,
    comment_id: Optional[int] = None,
) -> Optional[UsersMention]:
    """
    Ищет упоминания пользователей в тексте по регулярному выражению.

    Функция извлекает имена пользователей, упомянутых в тексте, используя шаблон MENTION_REGEX.
    Если текст отсутствует или упоминаний не найдено, возвращает None.

    :param type_mention: Тип упоминания (например, "post" или "comment").
    :param event_mention: Событие, связанное с упоминанием (например, "insert", "update").
    :param text: Текст, в котором ищутся упоминания.
    :param post_id: Идентификатор поста, в котором найдено упоминание (если применимо).
    :param comment_id: Идентификатор комментария, в котором найдено упоминание (если применимо).
    :return: Объект UsersMention с найденными именами пользователей и контекстом или None, если упоминаний нет.
    """
    if text is None or (
        (not (users := re.findall(MENTION_REGEX, text))) and event_mention != "update"
    ):
        return None

    return UsersMention(
        type_mention=type_mention,
        event_mention=event_mention,
        usernames=users,
        post_id=post_id,
        comment_id=comment_id,
    )


def publisher(
    rabbitmq_client: "RabbitMQClient",
    publisher_model: Any,
    logger_creator: Callable[[str], "Logger"],
    queue: str,
) -> None:
    """
    Публикует сообщение в указанную очередь RabbitMQ.

    :param rabbitmq_client: Клиент RabbitMQ для управления соединением.
    :param publisher_model: Pydantic-модель для сериализации в сообщение.
    :param logger_creator: Функция, создающая логгер по имени.
    :param queue: Название очереди RabbitMQ, в которую публикуется сообщение.

    :raises AMQPError: В случае ошибки публикации сообщение логируется и исключение пробрасывается.
    """
    log = logger_creator("publisher")
    try:
        log.info("Подготовка к публикации сообщения в очередь: %s", queue)
        with rabbitmq_client.get_connection() as connection:
            log.info("Соединение с RabbitMQ установлено.")
            with connection.channel() as channel:
                # Объявляем очередь, чтобы убедиться, что она существует
                channel.queue_declare(queue=queue, durable=True)
                log.info("Канал создан. Объявление очереди: %s", queue)

                # Сериализуем объект Pydantic в JSON и кодируем в байты
                message = publisher_model.model_dump_json(by_alias=True)
                log.info("Сообщение: %s готово к отправке", message)
                message_body = message.encode("utf-8")

                # Публикуем сообщение
                channel.basic_publish(
                    exchange="",
                    routing_key=queue,
                    body=message_body,
                    properties=BasicProperties(delivery_mode=2),  # persistent message
                )
    except AMQPError as err:
        log.exception(err)
    else:
        log.info("Сообщение опубликовано в очередь: %s", queue)


def outer_publisher(
    app: "CustomFastApi",
    publisher_model: Any,
) -> None:
    """
    Обёртка для публикации сообщения в RabbitMQ с использованием внешнего routing key.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ клиенту и логгеру.
    :param publisher_model: Pydantic-модель, которая будет сериализована и отправлена в очередь.
    """
    rabbitmq_client = app.get_rabbit_client()
    logger_creator = app.get_logger
    publisher(
        rabbitmq_client=rabbitmq_client,
        publisher_model=publisher_model,
        logger_creator=logger_creator,
        queue=rabbitmq_client.base_routing_key,
    )


def inner_publisher(
    app: "CustomFastApi",
    publisher_model: Any,
) -> None:
    """
    Обёртка для публикации сообщения в RabbitMQ с использованием внутреннего routing key.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ клиенту и логгеру.
    :param publisher_model: Pydantic-модель, которая будет сериализована и отправлена в очередь.
    """
    rabbitmq_client = app.get_rabbit_client()
    logger_creator = app.get_logger
    publisher(
        rabbitmq_client=rabbitmq_client,
        publisher_model=publisher_model,
        logger_creator=logger_creator,
        queue=rabbitmq_client.inner_routing_key,
    )
