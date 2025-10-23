from logging import Logger
from typing import Annotated

from dependencies.loger import get_loger
from dependencies.services import LikesServiceDep  # noqa: TC002
from fastapi import Depends, Path, Query
from routers.likes.access import ReadLikesUser  # noqa: TC002
from routers.likes.router import likes_router
from schemas.exception_schema import ErrorSchema
from schemas.likes import OutLikes, UserAddedLikeRead


@likes_router.get(
    "/news/post/{post_id}/likes",
    name="Получить id пользователей, которые поставили лайк посту.",
    description="Роут вернёт список из id пользователей, которые поставили указанному посту лайк. (с пагинацией)",
    response_model=OutLikes,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Пост не найден.",
            "model": ErrorSchema,
        },
    },
)
async def likes_post(
    post_id: Annotated[int, Path(..., gt=0)],
    likes_service: LikesServiceDep,
    log: Annotated[Logger, Depends(get_loger("likes_post"))],
    current_user: ReadLikesUser,
    page: Annotated[int, Query(..., gt=0)] = 1,
    limit: Annotated[int, Query(..., gt=0, le=100)] = 10,
) -> OutLikes:
    """
    Эндпоинт для получения списка лайков (ID пользователей), поставленных указанному посту, с пагинацией.

    :param post_id: Идентификатор поста.
    :param likes_service: Сервис для работы с лайками.
    :param log: Логгер для записи логов.
    :param current_user: Текущий пользователь.
    :param page: Номер страницы (по умолчанию 1).
    :param limit: Количество элементов на странице (по умолчанию 10, максимум 100).
    :return: Объект OutLikes с лайками.
    """

    log.info(
        "Пользователь с id=%s запрашивает информацию о лайках у поста с id=%s",
        current_user.id,
        post_id,
    )
    likes, count_pages = await likes_service.get_likes_post_with_pagination(
        page, limit, post_id
    )
    log.info(
        "Информация о лайках успешно возвращена пользователю. Пользователь: id=%s, пост id=%s",
        current_user.id,
        post_id,
    )

    return OutLikes(
        likes=[UserAddedLikeRead.model_validate(like) for like in likes],
        count_pages=count_pages,
    )
