from typing import TYPE_CHECKING, Optional

from events.utils import outer_publisher, search_for_users_mention

if TYPE_CHECKING:

    from core.classes.app import CustomFastApi
    from database.models import Comments, Posts


def users_mention(
    app: "CustomFastApi",
    type_mention: str,
    event_mention: str,
    text: Optional[str],
    post_id: int,
    comment_id: Optional[int] = None,
) -> None:
    """
    Обрабатывает упоминания пользователей в тексте и публикует событие в очередь.

    Производит поиск упоминаний пользователей в тексте с учётом типа и события,
    затем асинхронно публикует результат через outer_publisher.

    :param app: Экземпляр приложения CustomFastApi для доступа к сервисам.
    :param type_mention: Тип упоминания (например, "post" или "comment").
    :param event_mention: Событие упоминания (например, "create", "update", "delete").
    :param text: Текст, в котором ищутся упоминания.
    :param post_id: Идентификатор поста, к которому относится упоминание.
    :param comment_id: Опциональный идентификатор комментария, если упоминание связано с комментарием.
    """
    mentions = search_for_users_mention(
        type_mention, event_mention, text, post_id, comment_id
    )
    if not mentions:
        return

    outer_publisher(app, mentions)


def users_mention_comment_create(app: "CustomFastApi", new_comment: "Comments") -> None:
    """
    Обрабатывает упоминания пользователей при создании нового комментария.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param new_comment: Объект комментария, содержащий текст и идентификаторы.
    """
    users_mention(
        app=app,
        type_mention="comment",
        event_mention="create",
        text=new_comment.comment,
        post_id=new_comment.post_id,
        comment_id=new_comment.id,
    )


def users_mention_comment_delete(app: "CustomFastApi", comment: "Comments") -> None:
    """
    Обрабатывает удаление упоминаний пользователей при удалении комментария.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param comment: Объект комментария, содержащий текст и идентификаторы.
    """
    users_mention(
        app=app,
        type_mention="comment",
        event_mention="delete",
        text=comment.comment,
        post_id=comment.post_id,
        comment_id=comment.id,
    )


def users_mention_comment_update(
    app: "CustomFastApi", updated_comment: "Comments"
) -> None:
    """
    Обрабатывает обновление упоминаний пользователей при изменении комментария.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param updated_comment: Объект комментария с обновлённым текстом и идентификаторами.
    """
    users_mention(
        app=app,
        type_mention="comment",
        event_mention="update",
        text=updated_comment.comment,
        post_id=updated_comment.post_id,
        comment_id=updated_comment.id,
    )


def users_mention_post_create(app: "CustomFastApi", post: "Posts") -> None:
    """
    Обрабатывает упоминания пользователей при создании нового поста.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param post: Объект поста, содержащий текст и идентификатор.
    """
    users_mention(
        app=app,
        type_mention="post",
        event_mention="create",
        text=post.content,
        post_id=post.id,
    )


def users_mention_post_delete(app: "CustomFastApi", post: "Posts") -> None:
    """
    Обрабатывает удаление упоминаний пользователей при удалении поста.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param post: Объект поста, содержащий текст и идентификатор.
    """
    users_mention(
        app=app,
        type_mention="post",
        event_mention="delete",
        text=post.content,
        post_id=post.id,
    )


def users_mention_post_update(app: "CustomFastApi", post: "Posts") -> None:
    """
    Обрабатывает обновление упоминаний пользователей при изменении поста.

    :param app: Экземпляр приложения CustomFastApi для доступа к RabbitMQ и логированию.
    :param post: Объект поста, содержащий текст и идентификатор.
    """
    users_mention(
        app=app,
        type_mention="post",
        event_mention="update",
        text=post.content,
        post_id=post.id,
    )
