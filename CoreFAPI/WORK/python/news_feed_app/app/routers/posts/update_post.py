from logging import Logger
from typing import Annotated

from app_utils.permission import admin_role
from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from events.users_mention import users_mention_post_update
from fastapi import BackgroundTasks, Body, Depends, Path
from routers.posts.access import PostUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.exception_schema import ErrorSchema
from schemas.posts import PostUpdate, ShortOutPost, ShortPostRead


@posts_router.patch(
    "/news/post/{post_id}",
    response_model=ShortOutPost,
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
            "description": "Нельзя обновить пост, на который уже сделали репост.",
            "model": ErrorSchema,
        },
    },
    name="Обновить новость",
    description="Обновить новость. Если кто-то сделал репост новости, то обновить не получится.",
)
async def update_post_by_id(
    log: Annotated[Logger, Depends(get_loger("update_post_by_id"))],
    post_id: Annotated[int, Path(..., gt=0)],
    post_in: Annotated[PostUpdate, Body(...)],
    posts_service: PostsServiceDep,
    user: PostUser,
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> ShortOutPost:
    """
    Обновляет новость с указанным post_id.

    Проверяет права пользователя (владелец или админ с повышенными правами),
    запрещает обновление, если есть репосты (сервис выбрасывает ошибку 400),
    обновляет пост, коммитит изменения,
    запускает фоновую задачу для обновления упоминаний,
    возвращает сериализованный обновлённый пост.

    :param log: Логгер для записи действий.
    :param post_id: Идентификатор поста для обновления.
    :param post_in: Входные данные для обновления поста.
    :param posts_service: Сервис для работы с постами.
    :param user: Текущий аутентифицированный пользователь.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Объект ShortOutPost с данными обновлённого поста.
    """

    log.info("Начинаю обновление новости.")
    post = await posts_service.update(
        post_in, post_id, user, allowed_roles=[admin_role]
    )
    await posts_service.repo.commit()

    log.info("Новость с id=%s успешно обновлена", post.id)
    background_tasks.add_task(users_mention_post_update, app, post)

    return ShortOutPost(post=ShortPostRead.model_validate(post))
