from logging import Logger
from typing import Annotated

from app_utils.permission import admin_role
from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import CommentsServiceDep  # noqa: TC002
from events.users_mention import users_mention_comment_delete
from fastapi import BackgroundTasks, Depends, Path
from routers.comments.access import CommentsUser  # noqa: TC002
from routers.comments.router import comments_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@comments_router.delete(
    "/news/post/comment/{comment_id}",
    name="Удалить комментарий.",
    description="Удалить комментарий может только владелец или админ.",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Комментарий не найден.",
            "model": ErrorSchema,
        },
    },
)
async def delete_comment(
    comment_id: Annotated[int, Path(..., gt=0)],
    comment_service: CommentsServiceDep,
    current_user: CommentsUser,
    log: Annotated[Logger, Depends(get_loger("delete_comment"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Удаляет комментарий с указанным comment_id.

    Проверяет права текущего пользователя (владелец или админ),
    удаляет комментарий через сервис,
    запускает фоновую задачу для обработки удаления упоминаний,
    возвращает подтверждение успешного удаления.

    :param comment_id: Идентификатор комментария для удаления.
    :param comment_service: Сервис для работы с комментариями.
    :param current_user: Текущий аутентифицированный пользователь.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Подтверждение успешного удаления (BaseSchema).
    """
    undeleted_comment = await comment_service.repo.get_or_404(comment_id)

    log.info(
        "Пользователь с id=%s пытается удалить комментарий с id=%s",
        current_user.id,
        undeleted_comment.id,
    )
    await comment_service.delete_comment(
        undeleted_comment, user=current_user, allowed_roles=[admin_role]
    )
    log.info(
        "Комментарий с id=%s успешно удалён пользователем с id=%s",
        undeleted_comment.id,
        current_user.id,
    )
    background_tasks.add_task(users_mention_comment_delete, app, undeleted_comment)

    return BaseSchema()
