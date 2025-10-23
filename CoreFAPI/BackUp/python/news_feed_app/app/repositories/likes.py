from math import ceil
from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple

from database.models.likes import Likes
from repositories.base_repositories import BaseRepository
from sqlalchemy import func, select

if TYPE_CHECKING:
    from uuid import UUID


class LikesRepository(BaseRepository[Likes]):
    """
    Класс для работы с запросами к модели Likes.
    """

    type_model = Likes

    async def count_post_likes(self, post_id: int) -> int:
        """
         Подсчёт количества лайков на определенный пост.

        :param post_id: id поста
        :return: Количество лайков
        """

        likes_quantity = await self.get_filter(self.model.post_id == post_id)
        return len(likes_quantity)

    async def find_user_like_post(
        self, post_id: int, user_id: Optional["UUID"]
    ) -> Likes | None:
        """
         Находит лайк на конкретный пост пользователя.

        :param post_id:
        :param user_id: ID текущего пользователя
        :return: Объект модели лайков
        """
        if user_id is None:
            return None
        return await self.one_or_none(user_id=user_id, post_id=post_id)

    async def find_user_like_comment(
        self, comment_id: int, user_id: Optional["UUID"]
    ) -> Likes | None:
        """
        Поиск лайка текущего пользователя для указанного комментария.

        :param comment_id: Идентификатор комментария для проверки
        :param user_id: UUID аутентифицированного пользователя
        :return: Объект Likes или None, если лайк не найден
        """

        if user_id is None:
            return None
        return await self.one_or_none(user_id=user_id, comment_id=comment_id)

    async def create_and_save(self, data: dict[str, Any]) -> Likes:
        """
        Создаёт и сохраняет в базу новый лайк.

        :param data:
        :return: Объект модели лайков
        """
        new_like = self.create(data=data)
        await self.session.commit()
        return new_like

    async def get_likes_post_with_pagination(
        self, page: int, limit: int, post_id: int
    ) -> Tuple[Sequence[Likes], int]:
        """
        Получает лайки поста с пагинацией.

        :param page: Номер страницы (начинается с 1).
        :param limit: Количество лайков на странице.
        :param post_id: Идентификатор поста.
        :return: Кортеж из списка лайков и общего количества страниц.
        """
        total_stmt = select(func.count()).where(self.model.post_id == post_id)
        total_count = await self.session.scalar(total_stmt) or 0
        if not total_count:
            return [], 0
        pages_count = ceil(total_count / limit)

        result = await self.session.execute(
            select(self.model)
            .where(self.model.post_id == post_id)
            .offset((page - 1) * limit)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all(), pages_count

    async def get_likes_comment_with_pagination(
        self, page: int, limit: int, comment_id: int
    ) -> Tuple[Sequence[Likes], int]:
        """
        Получает лайки комментария с пагинацией.

        :param page: Номер страницы (начинается с 1).
        :param limit: Количество лайков на странице.
        :param comment_id: Идентификатор комментария.
        :return: Кортеж из списка лайков и общего количества страниц.
        """
        total_stmt = select(func.count()).where(self.model.comment_id == comment_id)
        total_count = await self.session.scalar(total_stmt) or 0
        if not total_count:
            return [], 0
        pages_count = ceil(total_count / limit)

        result = await self.session.execute(
            select(self.model)
            .where(self.model.comment_id == comment_id)
            .offset((page - 1) * limit)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all(), pages_count
