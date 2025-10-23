from typing import TYPE_CHECKING

from events.utils import inner_publisher
from schemas.author_weight import AuthorWeightRabbit, PreAuthorWeightRabbit

if TYPE_CHECKING:
    from uuid import UUID

    from core.classes.app import CustomFastApi


def author_weight(
    app: "CustomFastApi",
    user_id: "UUID",
    author_id: "UUID",
    weight: int,
) -> None:
    """
    Отправляет событие изменения веса автора в RabbitMQ.

    Создаёт модель AuthorWeightRabbit с указанными параметрами
    и публикует её через inner_publisher.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param user_id: UUID пользователя, для которого рассчитывается вес.
    :param author_id: UUID автора, чей вес изменяется.
    :param weight: Значение веса (целое число).
    """
    rabbit_model = AuthorWeightRabbit(
        user_id=user_id,
        author_id=author_id,
        weight=weight,
    )
    inner_publisher(app, rabbit_model)


def pre_author_weight(
    app: "CustomFastApi", user_id: "UUID", post_id: int, weight: int
) -> None:
    """
    Отправляет событие предварительного веса автора в RabbitMQ асинхронно.

    Создаёт модель PreAuthorWeightRabbit с указанными параметрами,
    затем публикует сообщение через inner_publisher в отдельном потоке.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param user_id: UUID пользователя, для которого рассчитывается вес.
    :param post_id: Идентификатор поста.
    :param weight: Значение предварительного веса.
    """
    rabbit_model = PreAuthorWeightRabbit(
        user_id=user_id,
        post_id=post_id,
        weight=weight,
    )
    inner_publisher(app, rabbit_model)
