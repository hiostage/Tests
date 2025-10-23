from logging import Logger
from typing import Annotated

from dependencies.loger import get_loger
from dependencies.services import LikesServiceDep  # noqa: TC002
from fastapi import Depends, Path
from routers.likes.access import LikesUser  # noqa: TC002
from routers.likes.router import likes_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@likes_router.delete(
    "/news/comment/{comment_id}/like",
    name="Убрать лайк комментарию.",
    description="Пользователь удалит свой лайк комментарию.",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        400: {
            "description": "Невозможно удалить лайк: лайк не существует.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Комментарий не найден.",
            "model": ErrorSchema,
        },
    },
)
async def dislike_comment(
    comment_id: Annotated[int, Path(..., gt=0)],
    likes_service: LikesServiceDep,
    current_user: LikesUser,
    log: Annotated[Logger, Depends(get_loger("dislike_comment"))],
) -> BaseSchema:
    """
    Обработчик удаления лайка с комментария.

    **Логика работы:**
    1. Проверка существования комментария (через метод сервиса)
    2. Поиск лайка пользователя
    3. Удаление лайка при его наличии
    4. Логирование результата

    :param comment_id: ID комментария (>0)
    :param likes_service: Сервис для работы с лайками
    :param current_user: Текущий аутентифицированный пользователь
    :param log: Логгер с контекстом 'dislike_comment'
    :return: BaseSchema
    :raises HTTPException: При ошибках валидации/доступа
    """
    log.info(
        "Пользователь с id=%s пытается удалить лайк комментарию с id=%s",
        current_user.id,
        comment_id,
    )
    await likes_service.delete_like_comment(user=current_user, comment_id=comment_id)
    await likes_service.repo.session.commit()
    log.info(
        "Пользователь с id=%s успешно убрал лайк с комментария с id=%s",
        current_user.id,
        comment_id,
    )

    return BaseSchema()
