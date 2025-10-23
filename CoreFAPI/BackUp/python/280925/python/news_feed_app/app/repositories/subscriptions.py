from typing import TYPE_CHECKING

from database.models import Subscriptions
from fastapi import HTTPException, status
from repositories.base_repositories import BaseRepository

if TYPE_CHECKING:
    from uuid import UUID


class SubscriptionsRepository(BaseRepository[Subscriptions]):
    """
    Репозиторий для работы с сущностью Subscriptions.
    """

    type_model = Subscriptions

    async def exists_subscriptions(self, user_id: "UUID", author_id: "UUID") -> bool:
        """
        Проверяет, существует ли подписка между указанным пользователем и автором.

        :param user_id: UUID пользователя, который подписывается.
        :param author_id: UUID автора, на которого подписываются.
        :return: True, если подписка существует, иначе False.
        """
        return await self.exists_by_data(
            self.model.user_id == user_id, self.model.author_id == author_id
        )

    async def get_subscription_or_404(
        self, user_id: "UUID", author_id: "UUID"
    ) -> Subscriptions:
        """
        Получает подписку пользователя на автора по их UUID.
        Если подписка не найдена, возбуждает HTTPException с кодом 404.

        :param user_id: UUID пользователя.
        :param author_id: UUID автора.
        :return: Объект подписки Subscriptions.
        :raises HTTPException: 404, если подписка не найдена.
        """
        subscription = await self.one_or_none(
            user_id=user_id,
            author_id=author_id,
        )
        if subscription is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Подписка пользователя с id={user_id} на автора с id={author_id} не найдена.",
            )
        return subscription
