from logging import Logger
from typing import Annotated

from app_utils.permission import admin_role
from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from events.users_mention import users_mention_post_delete
from fastapi import BackgroundTasks, Depends, Path
from routers.posts.access import PostUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@posts_router.delete(
    "/news/post/{post_id}",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Пост не найден.",
            "model": ErrorSchema,
        },
        400: {
            "description": "Нельзя удалить пост, если на него уже сделали репост. Нужен пользователь с повышенными правами.",
            "model": ErrorSchema,
        },
    },
    name="Удалить новость",
    description="Удалить новость может только владелец или админ. (Нельзя удалить пост, если на него уже сделали репост. Нужен пользователь с повышенными правами.)",
)
async def delete_post(
    log: Annotated[Logger, Depends(get_loger("delete_post"))],
    post_id: Annotated[int, Path(..., gt=0)],
    posts_service: PostsServiceDep,
    user: PostUser,
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Удаляет пост с указанным post_id.

    Проверяет права пользователя (владелец или админ с повышенными правами),
    запрещает удаление, если есть репосты (сервис выбрасывает ошибку 400),
    удаляет пост, коммитит изменения,
    запускает фоновую задачу для удаления упоминаний,
    возвращает подтверждение успешного удаления.

    :param log: Логгер для записи действий.
    :param post_id: Идентификатор поста для удаления.
    :param posts_service: Сервис для работы с постами.
    :param user: Текущий аутентифицированный пользователь.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Подтверждение успешного удаления (BaseSchema).
    """
    post = await posts_service.get_post_or_forbidden(
        post_id, user, allowed_roles=[admin_role]
    )
    log.info("Пользователь с id=%s пытается удалить пост с id=%s", user.id, post.id)
    await posts_service.delete(post)
    await posts_service.repo.commit()
    log.info("Пользователь с id=%s успешно удалил пост с id=%s", user.id, post.id)
    if post.content:
        background_tasks.add_task(users_mention_post_delete, app, post)
    return BaseSchema()
