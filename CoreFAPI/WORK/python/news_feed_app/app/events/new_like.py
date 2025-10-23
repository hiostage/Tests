from typing import TYPE_CHECKING, Optional

from events.utils import inner_publisher
from schemas.new_like import PreNewLikeRabbit

if TYPE_CHECKING:
    from uuid import UUID

    from core.classes.app import CustomFastApi


def pre_new_like(
    app: "CustomFastApi",
    user_id: "UUID",
    type_object: str,
    post_id: Optional[int] = None,
    comment_id: Optional[int] = None,
) -> None:
    """
    Отправляет событие предварительного уведомления о новом лайке в RabbitMQ.

    Создаёт модель PreNewLikeRabbit с указанными параметрами и публикует её через inner_publisher.

    :param app: Экземпляр приложения CustomFastApi для доступа к сервисам.
    :param user_id: UUID пользователя, поставившего лайк.
    :param type_object: Тип объекта, к которому поставлен лайк (например, "post" или "comment").
    :param post_id: Опциональный идентификатор поста.
    :param comment_id: Опциональный идентификатор комментария.
    """
    rabbit_model = PreNewLikeRabbit(
        user_id=user_id,
        post_id=post_id,
        type_object=type_object,
        comment_id=comment_id,
    )
    inner_publisher(app, rabbit_model)


def pre_new_like_post(app: "CustomFastApi", user_id: "UUID", post_id: int) -> None:
    """
    Отправляет событие предварительного уведомления о новом лайке поста.

    Вызывает функцию pre_new_like с параметрами для лайка поста.

    :param app: Экземпляр приложения CustomFastApi.
    :param user_id: UUID пользователя, поставившего лайк.
    :param post_id: Идентификатор поста, которому поставлен лайк.
    """
    pre_new_like(app=app, user_id=user_id, post_id=post_id, type_object="post")


def pre_new_like_comment(
    app: "CustomFastApi", user_id: "UUID", comment_id: int
) -> None:
    """
    Отправляет событие предварительного уведомления о новом лайке комментария.

    Вызывает функцию pre_new_like с параметрами для лайка комментария.

    :param app: Экземпляр приложения CustomFastApi.
    :param user_id: UUID пользователя, поставившего лайк.
    :param comment_id: Идентификатор комментария, которому поставлен лайк.
    """
    pre_new_like(app=app, user_id=user_id, comment_id=comment_id, type_object="comment")
