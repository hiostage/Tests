from typing import TYPE_CHECKING

from events.utils import inner_publisher
from schemas.hashtags_weight import PreHashtagsWeightRabbit

if TYPE_CHECKING:
    from uuid import UUID

    from core.classes.app import CustomFastApi


def pre_hashtags_weight(
    app: "CustomFastApi", user_id: "UUID", post_id: int, weight: int
) -> None:
    """
    Отправляет событие предварительного веса хештегов в RabbitMQ асинхронно.

    Создаёт модель PreHashtagsWeightRabbit с указанными параметрами,
    затем публикует сообщение через inner_publisher в отдельном потоке.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param user_id: UUID пользователя, для которого рассчитывается вес.
    :param post_id: Идентификатор поста.
    :param weight: Значение предварительного веса.
    """
    rabbit_model = PreHashtagsWeightRabbit(
        user_id=user_id,
        post_id=post_id,
        weight=weight,
    )
    inner_publisher(app, rabbit_model)
