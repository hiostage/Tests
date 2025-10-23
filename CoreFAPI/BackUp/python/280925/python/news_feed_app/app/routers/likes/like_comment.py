from logging import Logger
from typing import Annotated

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import LikesServiceDep  # noqa: TC002
from events.new_like import pre_new_like_comment
from fastapi import BackgroundTasks, Depends, Path
from routers.likes.access import LikesUser  # noqa: TC002
from routers.likes.router import likes_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@likes_router.post(
    "/news/comment/{comment_id}/like",
    name="Поставить лайк комментарию.",
    description="Пользователь поставит лайк комментарию, если он зарегистрирован в системе.",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        400: {
            "description": "Невозможно поставить лайк: лайк уже стоит.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Комментарий не найден.",
            "model": ErrorSchema,
        },
    },
)
async def like_comment(
    comment_id: Annotated[int, Path(..., gt=0)],
    likes_service: LikesServiceDep,
    current_user: LikesUser,
    log: Annotated[Logger, Depends(get_loger("like_comment"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Обрабатывает запрос на постановку лайка комментарию.

    Логирует попытку и успешное выполнение лайка,
    вызывает сервис для постановки лайка,
    запускает фоновую задачу для отправки уведомления о новом лайке.

    :param comment_id: Идентификатор комментария.
    :param likes_service: Сервис для работы с лайками.
    :param current_user: Текущий аутентифицированный пользователь.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Объект BaseSchema с результатом операции.
    """
    log.info(
        "Пользователь с id=%s пытается поставить лайк комментарию с id=%s",
        current_user.id,
        comment_id,
    )
    await likes_service.like_comment(user=current_user, comment_id=comment_id, log=log)
    log.info(
        "Пользователь с id=%s успешно поставил лайк комментарию с id=%s",
        current_user.id,
        comment_id,
    )
    if current_user.id:
        background_tasks.add_task(
            pre_new_like_comment,
            app=app,
            user_id=current_user.id,
            comment_id=comment_id,
        )
    return BaseSchema()
