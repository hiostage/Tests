from logging import Logger
from typing import Annotated

from dependencies.loger import get_loger
from dependencies.services import SubscriptionsServiceDep  # noqa: TC002
from fastapi import Depends, Query
from routers.subscriptions.access import SubscriptionsUser  # noqa: TC002
from routers.subscriptions.router import subscriptions_router
from schemas.exception_schema import ErrorSchema
from schemas.subscriptions import OutSubscriptions, SubscriptionRead


@subscriptions_router.get(
    "/news/subscriptions",
    name="Получение списка подписок пользователя.",
    description="Получает список подписок текущего пользователя с пагинацией.",
    response_model=OutSubscriptions,
    responses={
        403: {
            "description": "Доступ запрещён. Требуется аутентификация пользователя.",
            "model": ErrorSchema,
        },
    },
)
async def get_subscriptions(
    subscriptions_service: SubscriptionsServiceDep,
    current_user: SubscriptionsUser,
    log: Annotated[Logger, Depends(get_loger("get_subscription"))],
    page: Annotated[int, Query(..., gt=0)] = 1,
    limit: Annotated[int, Query(..., gt=0, le=100)] = 10,
) -> OutSubscriptions:
    """
    Получает список подписок текущего пользователя с пагинацией.

    :param subscriptions_service: Сервис для работы с подписками.
    :param current_user: Текущий аутентифицированный пользователь.
    :param log: Логгер для записи событий.
    :param page: Номер страницы (начинается с 1).
    :param limit: Количество подписок на странице (от 1 до 100).
    :return: Объект OutSubscriptions с подписками и информацией о количестве страниц.
    :raises HTTPException 403: Если пользователь не аутентифицирован.
    """
    log.info(
        "Пользователь с ID=%s запрашивает список подписок.",
        current_user.id,
    )
    result = await subscriptions_service.get_subscriptions(current_user, page, limit)
    log.info(
        "Список подписок для пользователя с ID=%s сформирован.",
        current_user.id,
    )

    return OutSubscriptions(
        count_pages=result.pages_count,
        subscriptions=[
            SubscriptionRead.model_validate(subscription)
            for subscription in result.subscriptions
        ],
    )
