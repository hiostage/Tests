from math import ceil
from typing import TYPE_CHECKING, Any, cast

from database.models import Subscriptions
from fastapi import HTTPException
from repositories.posts import PostsRepository
from repositories.subscriptions import SubscriptionsRepository
from services.base_service import BaseService
from services.posts import PostsService
from services.utils import SubscriptionsResult
from sqlalchemy import func, select

if TYPE_CHECKING:
    from uuid import UUID

    from schemas.users import User


class BaseSubscriptionsService(BaseService[SubscriptionsRepository]):
    """
    Базовый сервис для работы с подписками (Subscriptions).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__post_service = PostsService(
            repo=PostsRepository(session=self.repo.session)
        )

    @property
    def post_service(self) -> PostsService:
        """
        Сервис для работы с постами.

        :return: Экземпляр `PostsService` с общей сессией БД
        """
        return self.__post_service


class SubscriptionsService(BaseSubscriptionsService):
    """
    Сервис для работы с подписками (Subscriptions).
    """

    async def exists_author_or_404(self, author_id: "UUID") -> bool:
        """
        Проверяет, существует ли автор с указанным UUID.
        Если автор не найден (у него нет постов), выбрасывает исключение HTTPException с кодом 404.

        :param author_id: UUID автора, для которого выполняется проверка.
        :return: True, если автор найден.
        :raises HTTPException: 404, если автор не найден.
        """
        result = await self.post_service.exists_posts_by_author(author_id)
        if not result:
            raise HTTPException(
                status_code=404, detail="Автор с указанным UUID не найден."
            )
        return True

    async def create_subscription(
        self, user: "User", author_id: "UUID"
    ) -> Subscriptions:
        """
        Создаёт новую подписку пользователя на автора.

        :param user: Объект текущего пользователя, создающего подписку.
        :param author_id: UUID автора, на которого пользователь хочет подписаться.
        :return: Объект созданной подписки.
        :raises HTTPException: 400, если подписка уже существует.
        :raises HTTPException: 404, если автор с указанным UUID не найден.

        Логика:
        1. Проверяет, существует ли уже подписка между пользователем и автором.
        2. Если подписка есть - возбуждает ошибку 400.
        3. Проверяет существование автора, если нет - ошибка 404.
        4. Создаёт и добавляет новую подписку в сессию.
        """
        exists_subscription = await self.repo.exists_by_data(
            self.repo.model.user_id == user.id, self.repo.model.author_id == author_id
        )
        if exists_subscription:
            raise HTTPException(
                status_code=400, detail="Подписка уже была создана ранее."
            )
        await self.exists_author_or_404(author_id)
        subscription = Subscriptions(user_id=user.id, author_id=author_id)
        self.repo.session.add(subscription)
        return subscription

    async def delete_subscription(self, user: "User", author_id: "UUID") -> None:
        """
        Удаляет подписку пользователя на указанного автора.

        :param user: Объект текущего пользователя.
        :param author_id: UUID автора, от которого пользователь хочет отписаться.
        :raises HTTPException: 404, если подписка не найдена.
        """
        user_id = cast("UUID", user.id)
        subscription = await self.repo.get_subscription_or_404(
            user_id=user_id, author_id=author_id
        )
        await self.repo.session.delete(subscription)

    async def exists_subscription_or_404(self, user: "User", author_id: "UUID") -> bool:
        """
        Проверяет существование подписки пользователя на автора.
        Если подписка не найдена, выбрасывает HTTPException с кодом 404.

        :param user: Объект пользователя, для которого выполняется проверка.
        :param author_id: UUID автора, на которого проверяется подписка.
        :return: True, если подписка существует.
        :raises HTTPException: 404, если подписка не найдена.
        """
        return await self.repo.exists_or_404_by_data(
            self.repo.model.user_id == user.id, self.repo.model.author_id == author_id
        )

    async def get_subscriptions(
        self, user: "User", page: int, limit: int
    ) -> SubscriptionsResult:
        """
        Получает список подписок пользователя с пагинацией.

        :param user: Пользователь, чьи подписки запрашиваются.
        :param page: Номер страницы (начинается с 1).
        :param limit: Количество подписок на странице.
        :return: Объект SubscriptionsResult с подписками и количеством страниц.
        """
        total_count = await self.get_total_pages(user, limit)
        if total_count:
            subscriptions_q = await self.repo.session.execute(
                select(self.repo.model)
                .where(self.repo.model.user_id == user.id)
                .order_by(self.repo.model.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
            return SubscriptionsResult(
                subscriptions=subscriptions_q.scalars().all(), pages_count=total_count
            )
        return SubscriptionsResult(subscriptions=[], pages_count=total_count)

    async def get_total_pages(self, user: "User", limit: int) -> int:
        """
        Вычисляет общее количество страниц подписок пользователя с учётом лимита на страницу.

        :param user: Пользователь, для которого считаются подписки.
        :param limit: Максимальное количество подписок на одной странице.
        :return: Общее количество страниц (целое число).
        """
        count_stmt = (
            select(func.count())
            .select_from(self.repo.model)
            .where(self.repo.model.user_id == user.id)
        )

        total_count = await self.repo.session.scalar(count_stmt) or 0
        return ceil(total_count / limit)
