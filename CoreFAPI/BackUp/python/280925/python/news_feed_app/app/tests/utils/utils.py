import json
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from app_utils.rabbitmq_manager import RabbitMQClient


def rabbit_task_search(
    rabbitmq_client: "RabbitMQClient", **kwargs: Any
) -> Optional[Dict[str, Any]]:
    """
    Ищет в очереди RabbitMQ задачу (сообщение), которая соответствует заданным критериям.

    :param rabbitmq_client: Клиент для подключения к RabbitMQ.
    :param kwargs: Ключевые параметры для поиска в теле сообщения.
    :return: Найденное сообщение в виде словаря или None, если не найдено.
    """
    with rabbitmq_client.get_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_client.base_routing_key, durable=True)
        search_task = None

        while True:
            method, _, body = channel.basic_get(
                queue=rabbitmq_client.base_routing_key, auto_ack=True
            )
            if not method:
                break  # очередь пуста
            elif body:
                task = json.loads(body)
                if all(task.get(key) == value for key, value in kwargs.items()):
                    search_task = task
                    break
    return search_task
