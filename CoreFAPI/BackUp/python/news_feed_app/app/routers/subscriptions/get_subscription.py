from logging import Logger
from typing import Annotated
from uuid import UUID

from dependencies.loger import get_loger
from dependencies.services import SubscriptionsServiceDep  # noqa: TC002
from fastapi import Depends, Query
from routers.subscriptions.access import SubscriptionsUser  # noqa: TC002
from routers.subscriptions.router import subscriptions_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@subscriptions_router.get(
    "/news/subscription",
    name="Проверка подписки на автора.",
    description="Проверяет наличие активной подписки текущего пользователя на указанного автора по UUID.",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "Доступ запрещён. Требуется аутентификация пользователя.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Подписка не существует.",
            "model": ErrorSchema,
        },
    },
)
async def get_subscription(
    author_id: Annotated[UUID, Query(...)],
    subscriptions_service: SubscriptionsServiceDep,
    current_user: SubscriptionsUser,
    log: Annotated[Logger, Depends(get_loger("get_subscription"))],
) -> BaseSchema:
    """
    Проверяет существование подписки текущего пользователя на указанного автора.

    :param author_id: UUID автора для проверки подписки (передаётся в query-параметре).
    :param subscriptions_service: Сервис для работы с подписками.
    :param current_user: Аутентифицированный пользователь, для которого выполняется проверка.
    :param log: Логгер для записи событий.
    :return: BaseSchema с информацией о статусе подписки.
    :raises HTTPException 403: Если пользователь не аутентифицирован.
    :raises HTTPException 404: Если подписка не существуют.
    """
    log.info(
        "Пользователь с ID=%s пытается найти подписку на автора с ID=%s",
        current_user.id,
        author_id,
    )
    await subscriptions_service.exists_subscription_or_404(current_user, author_id)
    log.info(
        "Пользователь с ID=%s подписан на автора с ID=%s",
        current_user.id,
        author_id,
    )
    return BaseSchema()
