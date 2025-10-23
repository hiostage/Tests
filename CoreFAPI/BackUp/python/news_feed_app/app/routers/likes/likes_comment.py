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
    "/news/comment/{comment_id}/likes",
    name="Получить id пользователей, которые поставили лайк комментарию.",
    description="Роут вернёт список из id пользователей, которые поставили указанному комментарию лайк. (с пагинацией)",
    response_model=OutLikes,
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
async def likes_comment(
    comment_id: Annotated[int, Path(..., gt=0)],
    likes_service: LikesServiceDep,
    log: Annotated[Logger, Depends(get_loger("likes_comment"))],
    current_user: ReadLikesUser,
    page: Annotated[int, Query(..., gt=0)] = 1,
    limit: Annotated[int, Query(..., gt=0, le=100)] = 10,
) -> OutLikes:
    """
    Получение списка лайков комментария с пагинацией.

    :param comment_id: Идентификатор комментария (целое число > 0)
    :param likes_service: Сервис для работы с лайками
    :param log: Логгер для записи событий
    :param current_user: Пользователь
    :param page: Номер страницы пагинации (по умолчанию 1)
    :param limit: Количество элементов на странице (максимум 100)
    :return: Объект OutLikes с массивом лайков
    :raises HTTPException 403: При отсутствии прав доступа
    :raises HTTPException 404: При отсутствии комментария
    """

    log.info(
        "Пользователь с id=%s запрашивает информацию о лайках у комментария с id=%s",
        current_user.id,
        comment_id,
    )
    likes, count_pages = await likes_service.get_likes_comment_with_pagination(
        page=page, limit=limit, comment_id=comment_id
    )
    log.info(
        "Информация о лайках успешно возвращена пользователю. Пользователь: id=%s, комментарий id=%s",
        current_user.id,
        comment_id,
    )

    return OutLikes(
        likes=[UserAddedLikeRead.model_validate(like) for like in likes],
        count_pages=count_pages,
    )
