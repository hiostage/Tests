from logging import Logger
from typing import Annotated

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import CommentsServiceDep  # noqa: TC002
from events.new_comment import pre_new_comment
from events.users_mention import users_mention_comment_create
from fastapi import BackgroundTasks, Body, Depends, Path
from routers.comments.access import CommentsUser  # noqa: TC002
from routers.comments.router import comments_router
from schemas.comments import CommentCreate, ShortCommentRead, ShortOutComment
from schemas.exception_schema import ErrorSchema


@comments_router.post(
    "/news/post/{post_id}/comment",
    name="Написать комментарий к посту.",
    description="Создание комментария к указанному посту новостей.",
    response_model=ShortOutComment,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Пост не найден.",
            "model": ErrorSchema,
        },
        422: {
            "description": "Комментарий пустой или превышает ограничение по длине",
        },
    },
)
async def create_comment(
    post_id: Annotated[int, Path(..., gt=0)],
    comment_service: CommentsServiceDep,
    current_user: CommentsUser,
    comment: Annotated[CommentCreate, Body(...)],
    log: Annotated[Logger, Depends(get_loger("create_comment"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> ShortOutComment:
    """
    Создаёт комментарий к посту с указанным post_id.

    Проверяет существование поста, создаёт комментарий через сервис,
    запускает фоновые задачи для обработки упоминаний пользователей и уведомления о новом комментарии,
    возвращает созданный комментарий в формате ShortOutComment.

    :param post_id: Идентификатор поста, к которому добавляется комментарий.
    :param comment_service: Сервис для работы с комментариями.
    :param current_user: Текущий аутентифицированный пользователь.
    :param comment: Данные комментария, переданные в теле запроса.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Фоновый таск-менеджер FastAPI для неблокирующих задач.
    :return: Объект ShortOutComment с данными созданного комментария.
    """
    await comment_service.post_service.exists_post_or_404(post_id)
    log.info("Делаем запрос на создания комментария")
    new_comment = await comment_service.create_comment(
        post_id=post_id, user=current_user, comment=comment
    )
    log.info("Комментарий успешно создан")

    background_tasks.add_task(users_mention_comment_create, app, new_comment)
    background_tasks.add_task(
        pre_new_comment,
        app=app,
        user_id=new_comment.user_id,
        post_id=post_id,
        comment_id=new_comment.id,
    )
    return ShortOutComment(comment=ShortCommentRead.model_validate(new_comment))
