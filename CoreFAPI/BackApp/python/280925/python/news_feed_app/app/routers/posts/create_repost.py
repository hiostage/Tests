from logging import Logger
from typing import Annotated

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from events.new_post import pre_new_post
from events.users_mention import users_mention_post_create
from fastapi import BackgroundTasks, Body, Depends, Path
from routers.posts.access import PostUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.exception_schema import ErrorSchema
from schemas.posts import RePostCreate, ShortOutPost, ShortPostRead


@posts_router.post(
    "/news/post/{post_id}/repost",
    response_model=ShortOutPost,
    responses={
        403: {
            "description": "Недостаточно прав.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Оригинальный пост не найден",
            "model": ErrorSchema,
        },
    },
    name="Создание репоста",
    description="Создание репоста.",
)
async def create_repost(
    log: Annotated[Logger, Depends(get_loger("create_repost"))],
    post_id: Annotated[int, Path(..., gt=0)],
    repost_in: Annotated[RePostCreate, Body(...)],
    user: PostUser,
    posts_service: PostsServiceDep,
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> ShortOutPost:
    """
    Создаёт репост указанного поста.

    Логирует начало операции, создаёт репост через сервис,
    сохраняет изменения в базе, запускает фоновые задачи для обработки упоминаний
    и предварительного уведомления о новом посте,
    возвращает сериализованный созданный репост.

    :param log: Логгер для записи действий.
    :param post_id: Идентификатор оригинального поста.
    :param repost_in: Входные данные для создания репоста.
    :param user: Текущий аутентифицированный пользователь.
    :param posts_service: Сервис для работы с постами.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Объект ShortOutPost с данными созданного репоста.
    """

    log.info(
        "Пользователь id=%s. Начинаю создание репоста для поста id=%s", user.id, post_id
    )
    repost = await posts_service.create_repost(repost_in, user, post_id)
    await posts_service.repo.commit()
    log.info(
        "Пользователь id=%s. Репост успешно создан с id=%s",
        user.id,
        repost.id,
    )
    if repost.content:
        background_tasks.add_task(users_mention_post_create, app, repost)
    background_tasks.add_task(pre_new_post, app, repost.id, repost.user_id)

    return ShortOutPost(post=ShortPostRead.model_validate(repost))
