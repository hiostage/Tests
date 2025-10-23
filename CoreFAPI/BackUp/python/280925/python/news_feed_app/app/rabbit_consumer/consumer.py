from functools import partial
from typing import TYPE_CHECKING

from pika.exceptions import AMQPError
from rabbit_consumer.callback_func import callback_func

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi


def rabbit_consumer(app: "CustomFastApi") -> None:
    """
    Запускает потребителя сообщений RabbitMQ, который слушает очередь с внутренним ключом маршрутизации.

    Логирует основные этапы работы и обрабатывает исключения AMQP.

    :param app: Экземпляр приложения CustomFastApi.
    """
    log = app.get_logger("rabbit_consumer")
    rabbitmq_client = app.get_rabbit_client()

    log.info("Запускаю rabbit consumer")
    with rabbitmq_client.get_connection() as connection:
        log.info("Подключение создано")
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_client.inner_routing_key, durable=True)
        channel.basic_qos(prefetch_count=10)
        channel.basic_consume(
            queue=rabbitmq_client.inner_routing_key,
            on_message_callback=partial(callback_func, my_app=app),
        )
        try:
            channel.start_consuming()
        except AMQPError as err:
            log.exception(err)
