from logging import Logger
from typing import Annotated
from uuid import UUID

from dependencies.app import AppDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.services import SubscriptionsServiceDep  # noqa: TC002
from events.author_weight import author_weight
from events.new_subscriber import new_subscriber
from fastapi import BackgroundTasks, Depends, HTTPException, Query
from routers.subscriptions.access import SubscriptionsUser  # noqa: TC002
from routers.subscriptions.router import subscriptions_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@subscriptions_router.post(
    "/news/subscription",
    name="Подписаться на автора.",
    description="Позволяет текущему пользователю подписаться на указанного автора по его UUID. "
    "Важно: У автора должна быть опубликована хотя бы 1 статья, иначе 404.",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "Доступ запрещён. Пользователь не имеет прав для выполнения операции подписки.",
            "model": ErrorSchema,
        },
        400: {
            "description": "Некорректный запрос. "
            "Например, попытка подписаться на самого себя или оформить уже существующую подписку.",
            "model": ErrorSchema,
        },
        404: {
            "description": "Автор с указанным UUID не найден.",
            "model": ErrorSchema,
        },
    },
)
async def create_subscription(
    author_id: Annotated[UUID, Query(...)],
    subscriptions_service: SubscriptionsServiceDep,
    current_user: SubscriptionsUser,
    log: Annotated[Logger, Depends(get_loger("create_subscriptions"))],
    app: AppDep,
    background_tasks: BackgroundTasks,
) -> BaseSchema:
    """
    Позволяет текущему пользователю подписаться на указанного автора.

    Проверяет, что пользователь не подписывается на самого себя,
    создаёт подписку через сервис, коммитит изменения,
    запускает фоновые задачи для обновления веса автора и уведомления о новом подписчике,
    возвращает подтверждение успешной подписки.

    :param author_id: UUID автора, на которого подписываются.
    :param subscriptions_service: Сервис для работы с подписками.
    :param current_user: Текущий аутентифицированный пользователь.
    :param log: Логгер для записи действий.
    :param app: Экземпляр приложения для доступа к сервисам и публикации событий.
    :param background_tasks: Менеджер фоновых задач FastAPI.
    :return: Подтверждение успешной подписки (BaseSchema).
    """
    if current_user.id == author_id:
        raise HTTPException(
            status_code=400, detail="Нельзя подписаться на самого себя."
        )
    log.info(
        "Пользователь с ID=%s пытается подписаться на автора с ID=%s",
        current_user.id,
        author_id,
    )
    await subscriptions_service.create_subscription(current_user, author_id)
    await subscriptions_service.repo.commit()
    log.info(
        "Пользователь с ID=%s успешно подписался на автора с ID=%s",
        current_user.id,
        author_id,
    )
    if current_user.id:
        background_tasks.add_task(
            author_weight,
            app=app,
            user_id=current_user.id,
            author_id=author_id,
            weight=100,
        )
        background_tasks.add_task(
            new_subscriber,
            app=app,
            author_id=author_id,
            subscriber_id=current_user.id,
        )

    return BaseSchema()
