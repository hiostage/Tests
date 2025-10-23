from typing import TYPE_CHECKING

from events.utils import inner_publisher
from schemas.new_post import PreNewPostRabbit

if TYPE_CHECKING:
    from uuid import UUID

    from core.classes.app import CustomFastApi


def pre_new_post(app: "CustomFastApi", post_id: int, author_id: "UUID") -> None:
    """
    Отправляет событие предварительного уведомления о новом посте в RabbitMQ.

    Создаёт модель PreNewPostRabbit с указанными параметрами
    и публикует её через inner_publisher.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param post_id: Идентификатор созданного поста.
    :param author_id: UUID автора поста.
    """
    rabbit_model = PreNewPostRabbit(post_id=post_id, author_id=author_id)
    inner_publisher(app, rabbit_model)
