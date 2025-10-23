from math import ceil
from typing import TYPE_CHECKING, Any, Sequence, Tuple

from app_utils.permission import admin_role, check_me_or_role
from database.models import Comments, Likes
from fastapi import HTTPException, status
from repositories.comments import CommentsRepository
from repositories.posts import PostsRepository
from services.base_service import BaseService
from services.posts import PostsService
from services.utils import FilterResult
from sqlalchemy import exists, func, select
from sqlalchemy.exc import NoResultFound

if TYPE_CHECKING:

    from schemas.comments import CommentCreate
    from schemas.users import Role, User


class BaseCommentsService(BaseService[CommentsRepository]):
    """Базовый сервис для работы с комментариями"""

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


class CommentsService(BaseCommentsService):
    """
    Сервис для работы с комментариями
    """

    async def exists_comment_or_404(self, comment_id: int) -> bool:
        """
        Проверяет существование комментария, выбрасывая HTTP 404 при отсутствии.

        :param comment_id: Идентификатор комментария для проверки
        :return: True если комментарий существует
        :raises HTTPException 404: Если комментарий не найден
        """

        return await self.repo.exists_or_404(comment_id)

    async def create_comment(
        self, post_id: int, comment: "CommentCreate", user: "User"
    ) -> Comments:
        """
        Создаёт и сохраняет новый комментарий к указанному посту от пользователя.

        :param post_id: Идентификатор поста, к которому добавляется комментарий.
        :param comment: Объект с данными комментария (например, текст).
        :param user: Пользователь, создающий комментарий.
        :return: Созданный объект комментария.
        """
        data = comment.model_dump()
        data["post_id"] = post_id
        data["user_id"] = user.id
        return await self.repo.create_and_save(data=data)

    async def get_liked_comment_or_404(
        self, comment_id: int, user: "User"
    ) -> Tuple[Comments, bool]:
        """
        Получить комментарий по ID вместе с информацией, поставил ли текущий пользователь лайк.

        :param comment_id: ID комментария
        :param user: Объект пользователя
        :return: Кортеж (comment: Comments, is_liked_by_me: bool)
        :raises HTTPException 404: если комментарий не найден
        """
        stmt = select(
            self.repo.model,
            exists()
            .where((Likes.comment_id == comment_id) & (Likes.user_id == user.id))
            .label("is_liked_by_me"),
        ).where(Comments.id == comment_id)
        try:
            result = await self.repo.session.execute(stmt)
            comment, is_liked_by_me = result.one()
            return comment, is_liked_by_me
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Комментарий не найден")

    async def delete_comment(
        self,
        undeleted_comment: Comments,
        user: "User",
        allowed_roles: Sequence["Role"],
    ) -> None:
        """
        Удаляет комментарий и сохраняем результат в бд.
        Проверяет на право удаления комментария.

        :param undeleted_comment: Комментарий на удаление
        :param user: Пользователь, удаляющий комментарий
        :param allowed_roles: Роли пользователей, у которых есть право на удаления комментария
        :raise HTTPException 403: Пользователь не является автором комментария или администратором
        """
        if not check_me_or_role(user, undeleted_comment, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только автор или пользователь с повышенными правами может удалить комментарий.",
            )
        await self.repo.delete(undeleted_comment)
        await self.repo.commit()

    async def update_comment(
        self, comment_id: int, text: str, user: "User"
    ) -> Comments:
        """
        Обновляет текст комментария с проверкой прав пользователя.

        :param comment_id: Идентификатор комментария.
        :param text: Новый текст комментария.
        :param user: Пользователь, пытающийся обновить комментарий.
        :return: Обновлённый объект комментария.
        :raises HTTPException: Если пользователь не является автором или не имеет роли администратора.
        """

        comment = await self.repo.get_or_404(comment_id)
        if not check_me_or_role(user, comment, [admin_role]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только автор или пользователь с повышенными правами может изменить комментарий.",
            )
        comment.comment = text
        return comment

    async def get_comments(
        self, post_id: int, page: int, limit: int, user: "User"
    ) -> FilterResult[Comments]:
        """
        Получает комментарии к посту с пагинацией и флагом лайка текущего пользователя.

        Если комментариев нет, возвращает пустой результат и 0 страниц.

        :param post_id: Идентификатор поста.
        :param page: Номер страницы (начинается с 1).
        :param limit: Количество комментариев на странице.
        :param user: Текущий пользователь для проверки лайков.
        :return: FilterResult с кортежами (комментарий, is_liked_by_me) и количеством страниц.
        """

        # 1. Считаем общее количество комментариев
        total_stmt = select(func.count()).where(Comments.post_id == post_id)
        total_count = await self.repo.session.scalar(total_stmt) or 0
        if not total_count:
            return FilterResult(
                result=[],
                pages_count=0,
            )
        pages_count = ceil(total_count / limit)

        # 2. Получаем комментарии с флагом is_liked_by_me
        stmt = (
            select(
                self.repo.model,
                exists()
                .where((Likes.comment_id == Comments.id) & (Likes.user_id == user.id))
                .label("is_liked_by_me"),
            )
            .where(Comments.post_id == post_id)
            .order_by(Comments.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.repo.session.execute(stmt)
        items = result.all()
        return FilterResult(
            result=[(comment, is_liked_by_me) for comment, is_liked_by_me in items],
            pages_count=pages_count,
        )
