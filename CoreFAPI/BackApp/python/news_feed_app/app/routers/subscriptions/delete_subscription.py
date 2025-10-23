from logging import Logger
from typing import Annotated
from uuid import UUID

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import SubscriptionsServiceDep  # noqa: TC002
from events.author_weight import author_weight
from fastapi import BackgroundTasks, Depends, Query
from routers.subscriptions.access import SubscriptionsUser  # noqa: TC002
from routers.subscriptions.router import subscriptions_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@subscriptions_router.delete(
    "/news/subscription",
    name="Отписка от автора.",
    description="Позволяет текущему пользователю отписаться от указанного автора по его UUID.",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "Доступ запрещён. Пользователь не имеет прав для выполнения операции отписки.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Подписка не существует.",
            "model": ErrorSchema,
        },
    },
)
async def delete_subscription(
    author_id: Annotated[UUID, Query(...)],
    subscriptions_service: SubscriptionsServiceDep,
    current_user: SubscriptionsUser,
    log: Annotated[Logger, Depends(get_loger("delete_subscriptions"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Позволяет текущему пользователю отписаться от указанного автора.

    Логирует попытку отписки, удаляет подписку через сервис,
    коммитит изменения, запускает фоновую задачу для обновления веса автора,
    возвращает подтверждение успешной отписки.

    :param author_id: UUID автора, от которого отписываются.
    :param subscriptions_service: Сервис для работы с подписками.
    :param current_user: Текущий аутентифицированный пользователь.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Подтверждение успешной отписки (BaseSchema).
    """

    log.info(
        "Пользователь с ID=%s пытается отписаться от автора с ID=%s",
        current_user.id,
        author_id,
    )
    await subscriptions_service.delete_subscription(current_user, author_id)
    await subscriptions_service.repo.commit()
    log.info(
        "Пользователь с ID=%s успешно отписался от автора с ID=%s",
        current_user.id,
        author_id,
    )
    if current_user.id:
        background_tasks.add_task(
            author_weight,
            app=app,
            user_id=current_user.id,
            author_id=author_id,
            weight=-100,
        )

    return BaseSchema()
