from typing import TYPE_CHECKING, Any, Sequence, Tuple

from fastapi import HTTPException, status
from repositories.comments import CommentsRepository
from repositories.likes import LikesRepository
from services.base_service import BaseService
from services.comments import CommentsService

if TYPE_CHECKING:
    from logging import Logger
    from uuid import UUID

    from database.models import Likes
    from schemas.users import User
    from services.posts import PostsService


class BaseLikesService(BaseService[LikesRepository]):
    """
    Базовый сервис для работы с лайками.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__comment_service = CommentsService(
            repo=CommentsRepository(session=self.repo.session)
        )

    @property
    def post_service(self) -> "PostsService":
        """
        Сервис для работы с постами.

        :return: Экземпляр PostsService
        """
        return self.__comment_service.post_service

    @property
    def comment_service(self) -> CommentsService:
        """
        Сервис для работы с комментариями.

        :return: Экземпляр CommentsService
        """
        return self.__comment_service


class LikesService(BaseLikesService):
    """
    Сервис для работы с лайками.
    """

    async def like_post(self, user: "User", log: "Logger", post_id: int) -> "UUID":
        """
        Добавляет лайк в бд.

        :param user: Любой пользователь
        :param log: Логер для записи ошибок.
        :param post_id: Пост, который хотим пролайкать
        :return: id пользователя
        :raise: HTTPException если лайк найден в бд
        """
        like = await self.repo.find_user_like_post(user_id=user.id, post_id=post_id)
        if like:
            log.error("Ошибка лайк уже в базе %s", str(like.id))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно поставить лайк: лайк уже стоит.",
            )

        created_like = await self.repo.create_and_save(
            data=dict(post_id=post_id, user_id=user.id)
        )
        return created_like.user_id

    async def delete_like_post(self, user: "User", post_id: int) -> bool:
        """
        Удаляет лайк пользователя с указанного поста.

        Проверяет, существует ли лайк пользователя на посте.
        Если лайк не найден, выбрасывает HTTP 400 ошибку.
        Если найден - удаляет лайк и возвращает True.

        :param user: Объект пользователя, который удаляет лайк.
        :param post_id: Идентификатор поста.
        :return: True при успешном удалении лайка.
        :raises HTTPException: Если лайк не найден.
        """
        undeleted_like = await self.repo.find_user_like_post(
            user_id=user.id, post_id=post_id
        )
        if not undeleted_like:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить лайк: лайк не существует.",
            )
        await self.repo.delete(undeleted_like)
        return True

    async def get_likes_post_with_pagination(
        self, page: int, limit: int, post_id: int
    ) -> Tuple[Sequence["Likes"], int]:
        """
        Получает лайки поста с пагинацией, предварительно проверяя существование поста.

        :param page: Номер страницы (начинается с 1).
        :param limit: Количество лайков на странице.
        :param post_id: Идентификатор поста.
        :return: Кортеж из списка лайков и общего количества страниц.
        :raises HTTPException 404: Если пост с указанным ID не найден.
        """
        await self.post_service.exists_post_or_404(post_id)
        return await self.repo.get_likes_post_with_pagination(
            page=page, limit=limit, post_id=post_id
        )

    async def get_likes_comment_with_pagination(
        self, page: int, limit: int, comment_id: int
    ) -> Tuple[Sequence["Likes"], int]:
        """
        Получает лайки комментария с пагинацией, предварительно проверяя существование комментария.

        :param page: Номер страницы (начинается с 1).
        :param limit: Количество лайков на странице.
        :param comment_id: Идентификатор комментария.
        :return: Кортеж из списка лайков и общего количества страниц.
        :raises HTTPException 404: Если комментарий с указанным ID не найден.
        """
        await self.comment_service.exists_comment_or_404(comment_id)
        return await self.repo.get_likes_comment_with_pagination(
            page=page, limit=limit, comment_id=comment_id
        )

    async def like_comment(self, user: "User", log: "Logger", comment_id: int) -> None:
        """
        Создание лайка на комментарии с проверкой дублирования.

        Шаги работы:
        1. Проверка существования комментария
        2. Поиск существующего лайка пользователя
        3. Создание нового лайка при отсутствии дубля

        :param user: Аутентифицированный пользователь
        :param log: Логгер для записи событий
        :param comment_id: Идентификатор целевого комментария
        :raises HTTPException 404: Если комментарий не существует
        :raises HTTPException 400: При попытке дублирования лайка
        """
        await self.comment_service.exists_comment_or_404(comment_id)
        like = await self.repo.find_user_like_comment(
            user_id=user.id, comment_id=comment_id
        )
        if like:
            log.error("Ошибка лайк уже в базе id=%s", like.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно поставить лайк: лайк уже стоит.",
            )
        await self.repo.create_and_save(
            data=dict(comment_id=comment_id, user_id=user.id)
        )

    async def delete_like_comment(self, user: "User", comment_id: int) -> None:
        """
        Удаление лайка комментария (удаляет только из сессии, нужно явно подтвердить изменения).

        Шаги работы:
        1. Проверка существования комментария
        2. Поиск лайка текущего пользователя
        3. Удаление лайка при его наличии

        :param user: Аутентифицированный пользователь
        :param comment_id: Идентификатор комментария
        :raises HTTPException 404: Если комментарий не существует
        :raises HTTPException 400: Если лайк не найден
        """
        await self.comment_service.exists_comment_or_404(comment_id)
        like = await self.repo.find_user_like_comment(
            user_id=user.id, comment_id=comment_id
        )
        if not like:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить лайк: лайк не существует.",
            )
        await self.repo.delete(like)
