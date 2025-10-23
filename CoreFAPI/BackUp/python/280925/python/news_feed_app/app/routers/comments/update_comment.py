from logging import Logger
from typing import Annotated

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import CommentsServiceDep  # noqa: TC002
from events.users_mention import users_mention_comment_update
from fastapi import BackgroundTasks, Body, Depends, Path
from routers.comments.access import CommentsUser  # noqa: TC002
from routers.comments.router import comments_router
from schemas.base import BaseSchema
from schemas.comments import CommentCreate
from schemas.exception_schema import ErrorSchema


@comments_router.patch(
    "/news/post/comment/{comment_id}",
    name="Обновить комментарий",
    description="Обновляет текст существующего комментария по его идентификатору.",
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
        422: {
            "description": "Комментарий пустой или превышает ограничение по длине",
        },
    },
)
async def update_comment(
    comment_id: Annotated[int, Path(..., gt=0)],
    comment_service: CommentsServiceDep,
    current_user: CommentsUser,
    comment: Annotated[CommentCreate, Body(...)],
    log: Annotated[Logger, Depends(get_loger("update_comment"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Обновляет текст комментария с указанным comment_id.

    Проверяет права пользователя, обновляет комментарий через сервис,
    коммитит изменения, запускает фоновую задачу для обработки упоминаний,
    возвращает подтверждение успешного обновления.

    :param comment_id: Идентификатор комментария для обновления.
    :param comment_service: Сервис для работы с комментариями.
    :param current_user: Текущий аутентифицированный пользователь.
    :param comment: Данные комментария, переданные в теле запроса.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Подтверждение успешного обновления (BaseSchema).
    """
    log.info(
        "Пользователь с ID=%s пытается редактировать комментарий с ID=%s",
        current_user.id,
        comment_id,
    )
    updated_comment = await comment_service.update_comment(
        comment_id, comment.comment, current_user
    )
    await comment_service.repo.commit()
    log.info(
        "Пользователь с ID=%s успешно изменил комментарий с ID=%s",
        current_user.id,
        comment_id,
    )
    background_tasks.add_task(users_mention_comment_update, app, updated_comment)

    return BaseSchema()
