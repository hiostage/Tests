from typing import TYPE_CHECKING

from events.utils import outer_publisher
from schemas.new_subscriber import NewSubscriberRabbit

if TYPE_CHECKING:
    from uuid import UUID

    from core.classes.app import CustomFastApi


def new_subscriber(
    app: "CustomFastApi", author_id: "UUID", subscriber_id: "UUID"
) -> None:
    """
    Отправляет сообщение о новом подписчике в RabbitMQ асинхронно.

    Создаёт модель NewSubscriberRabbit с указанными идентификаторами автора и подписчика,
    затем запускает публикацию сообщения в отдельном потоке, не блокируя основной поток.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param author_id: UUID автора, на которого подписываются.
    :param subscriber_id: UUID пользователя, который подписался.
    """
    rabbit_model = NewSubscriberRabbit(author_id=author_id, subscriber_id=subscriber_id)
    outer_publisher(app, rabbit_model)
