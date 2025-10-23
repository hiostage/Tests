from logging import Logger
from typing import Annotated

from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from fastapi import Depends, Path
from routers.posts.access import PostReadUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.exception_schema import ErrorSchema
from schemas.posts import OutPost, PostRead


@posts_router.get(
    "/news/post/{post_id}",
    response_model=OutPost,
    responses={
        404: {
            "description": "Пост не найден.",
            "model": ErrorSchema,
        },
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
    },
    name="Получить новость",
    description="Получить новость.",
)
async def get_post_by_id(
    log: Annotated[Logger, Depends(get_loger("get_post_by_id"))],
    post_id: Annotated[int, Path(..., gt=0)],
    posts_service: PostsServiceDep,
    user: PostReadUser,
) -> OutPost:
    """
    Получить детальную информацию о новости по её идентификатору.

    :param log: Логгер для записи событий (автоматически внедряется).
    :param post_id: Идентификатор новости (должен быть больше 0).
    :param posts_service: Сервис для работы с новостями (автоматически внедряется).
    :param user: Текущий пользователь (автоматически внедряется).

    :return: Объект новости.

    :raises HTTPException 404: Если новость с указанным ID не найдена.
    """

    log.info("Начинаю поиск в БД ")
    post, is_liked = await posts_service.get_post_with_liked_current_user_or_404(
        post_id, user
    )
    log.info(
        "Запись в БД успешно найдена с id=%s.",
        post.id,
    )
    out_post = PostRead.model_validate(post)
    out_post.is_liked_by_me = is_liked
    return OutPost(post=out_post)
