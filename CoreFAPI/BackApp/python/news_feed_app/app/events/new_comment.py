from typing import TYPE_CHECKING

from events.utils import inner_publisher
from schemas.new_comment import PreNewCommentRabbit

if TYPE_CHECKING:
    from uuid import UUID

    from core.classes.app import CustomFastApi


def pre_new_comment(
    app: "CustomFastApi", user_id: "UUID", post_id: int, comment_id: int
) -> None:
    """
    Отправляет событие предварительного уведомления о новом комментарии в RabbitMQ асинхронно.

    Создаёт модель PreNewCommentRabbit с указанными параметрами,
    затем публикует сообщение через outer_publisher в отдельном потоке.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param user_id: UUID пользователя, который оставил комментарий.
    :param post_id: Идентификатор поста.
    :param comment_id: Идентификатор комментария.
    """
    rabbit_model = PreNewCommentRabbit(
        post_id=post_id, comment_id=comment_id, user_id=user_id
    )
    inner_publisher(app, rabbit_model)
