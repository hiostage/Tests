from logging import Logger
from typing import Annotated

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from events.new_post import pre_new_post
from events.users_mention import users_mention_post_create
from fastapi import BackgroundTasks, Body, Depends
from routers.posts.access import PostUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.exception_schema import ErrorSchema
from schemas.posts import PostCreate, ShortOutPost, ShortPostRead


@posts_router.post(
    "/news/post",
    response_model=ShortOutPost,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        }
    },
    name="Создание новости",
    description="Создание новости.",
)
async def create_post(
    log: Annotated[Logger, Depends(get_loger("create_post"))],
    post_in: Annotated[PostCreate, Body(...)],
    user: PostUser,
    posts_service: PostsServiceDep,
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> ShortOutPost:
    """
    Создаёт новую новость (пост).

    Логирует начало операции, создаёт пост через сервис,
    сохраняет изменения в базе, запускает фоновые задачи для обработки упоминаний
    и предварительного уведомления о новом посте,
    возвращает сериализованный созданный пост.

    :param log: Логгер для записи действий.
    :param post_in: Входные данные для создания поста.
    :param user: Текущий аутентифицированный пользователь.
    :param posts_service: Сервис для работы с постами.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Объект ShortOutPost с данными созданного поста.
    """
    log.info("Начинаю делать запись в БД ")
    post = await posts_service.create(post_in, user)
    await posts_service.repo.commit()
    log.info(
        "Запись в БД успешно добавлена с id=%s.",
        post.id,
    )
    if post.content:
        background_tasks.add_task(users_mention_post_create, app, post)
    background_tasks.add_task(pre_new_post, app, post.id, post.user_id)

    return ShortOutPost(post=ShortPostRead.model_validate(post))
