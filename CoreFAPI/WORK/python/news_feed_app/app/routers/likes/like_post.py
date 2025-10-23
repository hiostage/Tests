from logging import Logger
from typing import Annotated

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import LikesServiceDep  # noqa: TC002
from events.author_weight import pre_author_weight
from events.hashtags_weight import pre_hashtags_weight
from events.new_like import pre_new_like_post
from fastapi import BackgroundTasks, Depends, Path
from routers.likes.access import LikesUser  # noqa: TC002
from routers.likes.router import likes_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@likes_router.post(
    "/news/post/{post_id}/like",
    name="Поставить лайк посту.",
    description="Пользователь поставит лайк посту, если он зарегистрирован в системе.",
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
            "description": "Пост не найден.",
            "model": ErrorSchema,
        },
    },
)
async def like_post(
    post_id: Annotated[int, Path(..., gt=0)],
    likes_service: LikesServiceDep,
    current_user: LikesUser,
    log: Annotated[Logger, Depends(get_loger("like_post"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Ставит лайк пользователем на указанный пост.

    Проверяет существование поста, добавляет лайк в базу,
    запускает фоновые задачи для обновления веса автора и хештегов,
    возвращает подтверждение успешного добавления лайка.

    :param post_id: Идентификатор поста для лайка.
    :param likes_service: Сервис для работы с лайками.
    :param current_user: Текущий аутентифицированный пользователь.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Подтверждение успешного добавления (BaseSchema).
    """

    await likes_service.post_service.exists_post_or_404(post_id)
    log.info("Записываем лайк поста в бд")
    await likes_service.like_post(user=current_user, log=log, post_id=post_id)
    log.info("Лайк поста записан в бд")
    if current_user.id:
        background_tasks.add_task(
            pre_author_weight,
            app=app,
            user_id=current_user.id,
            post_id=post_id,
            weight=1,
        )
        background_tasks.add_task(
            pre_hashtags_weight,
            app=app,
            user_id=current_user.id,
            post_id=post_id,
            weight=1,
        )
        background_tasks.add_task(
            pre_new_like_post,
            app=app,
            user_id=current_user.id,
            post_id=post_id,
        )
    return BaseSchema()
