from logging import Logger
from typing import Annotated

from dependencies.loger import get_loger
from dependencies.services import CommentsServiceDep  # noqa: TC002
from fastapi import Depends, Path, Query
from routers.comments.access import ReadCommentsUser  # noqa: TC002
from routers.comments.router import comments_router
from schemas.comments import CommentRead, OutComments
from schemas.exception_schema import ErrorSchema


@comments_router.get(
    "/news/post/{post_id}/comments",
    name="Получение списка комментариев",
    description="Получение списка комментариев к посту с пагинацией.",
    response_model=OutComments,
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
async def get_comments(
    post_id: Annotated[int, Path(..., gt=0)],
    comment_service: CommentsServiceDep,
    current_user: ReadCommentsUser,
    log: Annotated[Logger, Depends(get_loger("get_comments"))],
    page: Annotated[int, Query(..., gt=0)] = 1,
    limit: Annotated[int, Query(..., gt=0, le=100)] = 10,
) -> OutComments:
    """
    Возвращает список комментариев к указанному посту с поддержкой пагинации.

    :param post_id: Идентификатор поста, к которому запрашиваются комментарии.
    :param comment_service: Сервис для работы с комментариями.
    :param current_user: Текущий пользователь с правами чтения комментариев.
    :param log: Логгер для записи действий.
    :param page: Номер страницы (начинается с 1).
    :param limit: Максимальное количество комментариев на странице (до 100).
    :return: Объект OutComments с комментариями и количеством страниц.
    :raises HTTPException 403: Если у пользователя нет прав доступа.
    :raises HTTPException 404: Если пост с указанным ID не найден.
    """
    await comment_service.post_service.exists_post_or_404(post_id)
    log.info(
        "Пользователь с ID=%s запрашивает %s страницу комментариев к посту с ID=%s",
        current_user.id,
        page,
        post_id,
    )
    result = await comment_service.get_comments(post_id, page, limit, current_user)
    log.info(
        "Пользователю с ID=%s успешно возвращается %s страница комментариев к посту с ID=%s",
        current_user.id,
        page,
        post_id,
    )
    response_comments_list = []
    for comment, liked in result.result:
        response_comment = CommentRead.model_validate(comment)
        response_comment.is_liked_by_me = liked
        response_comments_list.append(response_comment)
    return OutComments(count_pages=result.pages_count, comments=response_comments_list)
