from logging import Logger
from typing import Annotated

from dependencies.loger import get_loger
from dependencies.services import CommentsServiceDep  # noqa: TC002
from fastapi import Depends, Path
from routers.comments.access import ReadCommentsUser  # noqa: TC002
from routers.comments.router import comments_router
from schemas.comments import CommentRead, OutComment
from schemas.exception_schema import ErrorSchema


@comments_router.get(
    "/news/post/comment/{comment_id}",
    name="Получить комментарий по id",
    description="Получение полного описания комментария по его идентификатору.",
    response_model=OutComment,
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
async def get_comment(
    comment_id: Annotated[int, Path(..., gt=0)],
    comment_service: CommentsServiceDep,
    current_user: ReadCommentsUser,
    log: Annotated[Logger, Depends(get_loger("get_comment"))],
) -> OutComment:
    """
     Получает комментарий по идентификатору.

    :param comment_id: ID получаемоего комментария
    :param comment_service: Сервис для работы с комментариями
    :param current_user: Авторизованный пользователь (автоматически извлекается из запроса)
    :param log: Логгер для записи событий
    :return: Полная информация о комментарии с результатом
    """
    log.info("Запрашиваем данные у БД")
    comment, is_liked = await comment_service.get_liked_comment_or_404(
        comment_id, current_user
    )
    log.info(
        "Запись в БД успешно найдена с id=%s.",
        comment.id,
    )
    response_model = CommentRead.model_validate(comment)
    response_model.is_liked_by_me = is_liked
    return OutComment(comment=response_model)
