from math import ceil
from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Union

from app_utils.permission import admin_role, check_me_or_role
from database.models import AuthorWeight, HashtagWeight, Likes, Posts
from database.models.hashtags import PostHashtag
from fastapi import HTTPException, status
from repositories.attachments import AttachmentsRepository
from repositories.hashtags import HashtagsRepository
from repositories.posts import PostsRepository
from services.attachments import AttachmentsService
from services.base_service import BaseService
from services.hashtags_service import HashtagsService
from services.utils import (
    FilterResult,
    date_from_posts_filter,
    date_to_posts_filter,
    hashtags_posts_filter,
    inspect_object_lists,
    search_content_posts_filter,
    search_title_posts_filter,
    subscriptions_posts_filter,
    user_posts_filter,
)
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:

    from uuid import UUID

    from schemas.posts import FilterPosts, PostCreate, PostUpdate, RePostCreate
    from schemas.users import Role, User


class BasePostsService(BaseService[PostsRepository]):
    """
    Базовый сервис для работы с постами.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__att_service = AttachmentsService(
            repo=AttachmentsRepository(session=self.repo.session)
        )
        self.__hashtags_service = HashtagsService(
            repo=HashtagsRepository(session=self.repo.session)
        )

    @property
    def att_service(self) -> AttachmentsService:
        """
        Сервис для работы с вложениями.

        :return: Экземпляр AttachmentsService
        """
        return self.__att_service

    @property
    def hashtags_service(self) -> HashtagsService:
        """
        Сервис для работы с хэштегами.

        :return: Экземпляр HashtagsService
        """
        return self.__hashtags_service


class PostsService(BasePostsService):
    """
    Сервис для работы с постами.
    """

    async def create(
        self, post_create: Union["PostCreate", "RePostCreate"], user: "User"
    ) -> Posts:
        """
        Создаёт новый пост.

        :param post_create: Данные для создания поста
        :param user: Автор поста
        :return: Созданный пост
        """
        post_data = post_create.model_dump(exclude={"attachments_ids", "hashtag_names"})
        post = self.repo.model(**post_data, user_id=user.id)
        if post_create.attachments_ids:
            attachments = await self.att_service.get_by_ids_no_post(
                post_create.attachments_ids, user
            )
            post.attachments.extend(attachments)
        if post_create.hashtag_names:
            hashtags = await self.hashtags_service.get_or_create_by_hashtag_names(
                post_create.hashtag_names
            )
            post.hashtags.extend(hashtags)
        self.repo.session.add(post)
        return post

    async def get_post_with_repost_or_404(self, post_id: int) -> Posts:
        """
        Получает пост с информацией о репосте по ID или вызывает HTTP 404, если пост не найден.

        :param post_id: ID поста для поиска
        :return: Объект Posts с загруженным original_post (если есть)
        :raises HTTPException: с кодом 404, если пост не найден
        """
        post = await self.repo.get_post_with_repost(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пост с ID {post_id} не найден.",
            )
        return post

    async def create_repost(
        self, repost_create: "RePostCreate", user: "User", post_id: int
    ) -> Posts:
        """
        Создаёт репост для указанного поста с учётом содержимого и вложений.

        :param repost_create: Данные для создания репоста (контент, вложения и т.п.)
        :param user: Пользователь, создающий репост
        :param post_id: ID оригинального поста, который репостится
        :return: Созданный объект Posts, представляющий репост
        """
        post = await self.get_post_with_repost_or_404(post_id)
        repost = await self.create(repost_create, user)
        if not post.original_post or (
            (post.content is not None and post.content.strip()) or post.attachments
        ):
            repost.original_post = post
        else:
            repost.original_post = post.original_post

        return repost

    async def delete(self, post: Posts) -> None:
        """
        Удаляет пост.

        :param post: Пост для удаления
        """
        for attachment in post.attachments:
            attachment.is_deleted = True
        await self.repo.delete(post)

    async def get_post_or_404(self, post_id: int) -> Posts:
        """
        Возвращает пост по ID.

        :param post_id: ID поста
        :return: Пост
        :raises HTTPException 404: Если пост не найден
        """
        return await self.repo.get_or_404(post_id)

    async def get_post_with_liked_current_user_or_404(
        self, post_id: int, user: "User"
    ) -> tuple[Posts, bool]:
        """
        Асинхронно получает пост по его идентификатору и проверяет, лайкнул ли его текущий пользователь.

        :param post_id: Идентификатор поста.
        :param user: Текущий пользователь.

        :return: Кортеж, содержащий пост и флаг, указывающий, лайкнул ли его текущий пользователь.

        :raises HTTPException 404: Если пост с указанным ID не найден.
        """
        stmt = (
            select(
                self.repo.model,
                exists()
                .where((Likes.post_id == Posts.id) & (Likes.user_id == user.id))
                .label("is_liked_by_me"),
            )
            .where(Posts.id == post_id)
            .options(selectinload(Posts.original_post))
        )

        try:
            result = await self.repo.session.execute(stmt)
            post, is_liked = result.one()
            return post, is_liked
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Пост не найден")

    async def get_filter_posts_with_liked_current_user(
        self, user: "User", filter_posts: "FilterPosts"
    ) -> FilterResult[Posts]:
        """
        Получает список постов с применёнными фильтрами и информацией о лайке текущего пользователя, а также количеством страниц.

        Формирует SQL-запрос с выборкой постов и дополнительным булевым полем `is_liked_by_me`,
        указывающим, лайкнул ли текущий пользователь каждый пост. Применяет набор фильтров из
        объекта `filter_posts`, включая фильтрацию по автору, дате, заголовку, содержимому, хештегам и подпискам.

        Выполняет пагинацию на основе параметров `page` и `limit`, а также вычисляет общее количество страниц.

        :param user: Текущий пользователь, для которого проверяется наличие лайка на каждом посте.
        :param filter_posts: Объект с параметрами фильтрации и пагинации постов.
        :return: Экземпляр FilterResult с результатом выборки (список кортежей (Posts, bool)) и количеством страниц.
        """
        stmt = select(
            self.repo.model,
            exists()
            .where((Likes.post_id == Posts.id) & (Likes.user_id == user.id))
            .label("is_liked_by_me"),
        )
        filter_func_list = [
            user_posts_filter,
            date_from_posts_filter,
            date_to_posts_filter,
            search_title_posts_filter,
            search_content_posts_filter,
            hashtags_posts_filter,
            subscriptions_posts_filter,
        ]
        filter_list: List[Any] = []
        for filter_func in filter_func_list:
            stmt = filter_func(filter_list, filter_posts, stmt, user)

        if filter_list:
            stmt = stmt.where(and_(*filter_list))

        pages_count = await self.get_total_pages(filter_list, filter_posts)

        if pages_count:
            stmt = (
                stmt.options(selectinload(Posts.original_post))
                .order_by(self.repo.model.created_at.desc())
                .offset((filter_posts.page - 1) * filter_posts.limit)
                .limit(filter_posts.limit)
            )
            result = await self.repo.session.execute(stmt)
            return FilterResult(
                result=[(post, is_liked) for post, is_liked in result.all()],
                pages_count=pages_count,
            )
        return FilterResult(result=[], pages_count=pages_count)

    async def get_total_pages(
        self, filter_list: List[Any], filter_posts: "FilterPosts"
    ) -> int:
        """
        Вычисляет общее количество страниц для постов с учётом фильтров и лимита на страницу.

        Формирует SQL-запрос для подсчёта общего количества постов, удовлетворяющих условиям фильтрации.
        Делит общее количество постов на лимит (posts per page) и округляет вверх до ближайшего целого,
        чтобы получить количество страниц.

        :param filter_list: Список условий фильтрации для применения к запросу.
        :param filter_posts: Объект с параметрами фильтрации и лимитом на страницу.
        :return: Общее количество страниц (int).
        """
        count_stmt = select(func.count()).select_from(self.repo.model)
        if filter_list:
            count_stmt = count_stmt.where(and_(*filter_list))
        total_count = await self.repo.session.scalar(count_stmt) or 0
        return ceil(total_count / filter_posts.limit)

    async def exists_post_or_404(self, post_id: int) -> bool:
        """
        Проверяет существование поста в базе данных по его ID и возвращает True, если пост существует.
        Если пост не найден, возвращает ошибку 404.

        :param post_id: ID поста для проверки
        :return: True, если пост существует
        :raises HTTPException: Если пост не найден (404 Not Found)
        """
        return await self.repo.exists_or_404(post_id)

    async def get_post_or_forbidden(
        self, post_id: int, user: "User", allowed_roles: Sequence["Role"]
    ) -> Posts:
        """
        Получает пост по ID и проверяет права доступа пользователя.

        Функция пытается получить пост с заданным `post_id`. Если пост не найден,
        вызывается исключение 404 (через `get_post_or_404`). Далее проверяется,
        имеет ли пользователь `user` права доступа к посту на основе роли или
        принадлежности к владельцу поста. Если проверка не пройдена, выбрасывается
        ошибка 403 Forbidden.

        Дополнительно, если у поста есть репосты (`reposts_count > 0`), и пользователь
        не обладает ролью администратора, выбрасывается ошибка 400 Bad Request —
        нельзя удалить пост с репостами.

        :param post_id: Идентификатор поста для получения.
        :param user: Пользователь, пытающийся получить пост.
        :param allowed_roles: Последовательность ролей, которым разрешён доступ к посту.
        :raises HTTPException: 403 если нет прав доступа, 400 если пост с репостами нельзя удалить.
        :return: Объект поста `Posts`, если доступ разрешён.
        """
        post = await self.get_post_or_404(post_id)
        if not check_me_or_role(user, post, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только хозяин или пользователь с повышенными правами может получить доступ к посту.",
            )
        if post.reposts_count and admin_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить пост, если на него сделали репост.",
            )
        return post

    async def update(
        self,
        data: "PostUpdate",
        post_id: int,
        user: "User",
        allowed_roles: Sequence["Role"],
    ) -> Posts:
        """
        Обновляет пост с указанным ID.

        :param data: Данные для обновления поста
        :param post_id: ID поста для обновления
        :param user: Пользователь, обновляющий пост
        :param allowed_roles: Список ролей, которым разрешено обновлять пост
        :return: Обновлённый пост

        Процесс:
        1. Получает пост по ID, проверяя права доступа пользователя.
        2. Обновляет вложения, если переданы новые ID вложений.
        3. Обновляет хэштеги, если переданы новые имена хэштегов.
        4. Обновляет остальные данные поста.

        :raises HTTPException: Если пользователь не имеет доступа к посту (403 Forbidden)
        """

        # Получим пост
        post = await self.get_post_or_forbidden(post_id, user, allowed_roles)
        if post.reposts_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя обновить пост, если на него сделали репост.",
            )

        # ВЛОЖЕНИЯ:
        if data.attachments_ids is not None:
            await self.__update_attachments(post, data, user)

        # ХЕШТЕГИ:
        if data.hashtag_names is not None:
            await self.__update_hashtags(post, data)

        # ОСТАЛЬНЫЕ ДАННЫЕ
        update_data = data.model_dump(
            exclude_unset=True, exclude={"attachments_ids", "hashtag_names"}
        )
        for key, value in update_data.items():
            setattr(post, key, value)

        return post

    async def __update_attachments(
        self, post: Posts, data: "PostUpdate", user: "User"
    ) -> None:
        """
        Обновляет вложения поста.

        :param post: Пост, для которого обновляются вложения
        :param data: Данные для обновления поста
        :param user: Пользователь, обновляющий вложения

        Процесс:
        1. Сравнивает текущие вложения с новыми и определяет:
           - Удалённые вложения
           - Новые вложения
        2. Удаляет связи с удалёнными вложениями.
        3. Добавляет новые вложения.
        """
        # Отфильтруем новые, удалённые и неизменённые id вложений у поста
        if data.attachments_ids is None:
            raise ValueError("Передан None вместо List[int]")
        att_inspect_ids = inspect_object_lists(
            [att.id for att in post.attachments], data.attachments_ids
        )
        # Определим вложения для удаления
        delete_att = [
            att for att in post.attachments if att.id in att_inspect_ids.deleted_obj
        ]
        for att in delete_att:
            self.att_service.fake_delete(att)
        # Получим и добавим новые вложения
        if att_inspect_ids.new_obj:
            new_attachments = await self.att_service.get_by_ids_no_post(
                att_inspect_ids.new_obj, user
            )
            post.attachments.extend(new_attachments)

    async def __update_hashtags(self, post: Posts, data: "PostUpdate") -> None:
        """
        Обновляет хэштеги поста.

        :param post: Пост, для которого обновляются хэштеги
        :param data: Данные для обновления поста

        Процесс:
        1. Сравнивает текущие хэштеги с новыми и определяет:
           - Удалённые хэштеги
           - Новые хэштеги
        2. Удаляет связи с удалёнными хэштегами.
        3. Добавляет новые хэштеги.
        """
        if data.hashtag_names is None:
            raise ValueError("Передан None вместо List[str]")
        # Отфильтруем новые, удалённые и неизменённые хештеги у поста
        tag_inspect_name = inspect_object_lists(
            [tag.name for tag in post.hashtags], data.hashtag_names
        )
        # Удалим связи хештегов и поста, которые больше не используются
        delete_tags = [
            tag for tag in post.hashtags if tag.name in tag_inspect_name.deleted_obj
        ]
        for tag in delete_tags:
            post.hashtags.remove(tag)
        # Получим и добавим новые хештеги
        if tag_inspect_name.new_obj:
            new_hashtags = await self.hashtags_service.get_or_create_by_hashtag_names(
                tag_inspect_name.new_obj
            )
            post.hashtags.extend(new_hashtags)

    async def exists_posts_by_author(self, author_id: "UUID") -> bool:
        """
        Проверяет, существуют ли посты у указанного автора.

        :param author_id: UUID автора, для которого выполняется проверка.
        :return: True, если у автора есть хотя бы один пост, иначе False.
        """
        return await self.repo.exists_by_data(self.repo.model.user_id == author_id)

    async def get_personalized_feed(
        self, user_id: Optional["UUID"], limit: int, page: int
    ) -> FilterResult[Posts]:
        """
        Получает персонализированную ленту постов с учётом весов авторов и хештегов.

        Логика работы:
        1. Проверяет наличие хештегов с весом >= MIN_WEIGHT_HASHTAG (30)
        2. Если таких хештегов нет:
           - Возвращает все посты, отсортированные по дате создания
           - Добавляет информацию о лайках пользователя
           - Рассчитывает общее количество постов для пагинации
        3. При наличии подходящих хештегов:
           - Формирует сложный запрос с учётом минимальных порогов:
             * MIN_WEIGHT_AUTHOR (5) - минимальный вес автора
             * MIN_SUM_WEIGHT_HASHTAGS (15) - минимальная сумма весов хештегов
           - Исключает посты, не соответствующие порогам
           - Сортирует по приоритету: дата → вес автора → сумма хештегов
           - Добавляет информацию о лайках и рассчитывает пагинацию

        Параметры:
        :param user_id: UUID пользователя
        :param limit: Количество постов на странице
        :param page: Страница
        :return: FilterPostsResult (посты + метаданные пагинации)
        """

        # Основное условие для начала персонализации:
        MIN_WEIGHT_HASHTAG = 30
        # Условие выборки персонализации через ИЛИ (1 условие должно быть True)
        MIN_SUM_WEIGHT_HASHTAGS = 15
        MIN_WEIGHT_AUTHOR = 5
        # Шаг 1: Проверяем, есть ли хотя бы один вес хештега >= MIN_WEIGHT_HASHTAG
        has_enough_weight: bool = False
        if user_id:
            check_stmt = (
                select(HashtagWeight)
                .where(
                    HashtagWeight.user_id == user_id,
                    HashtagWeight.weight >= MIN_WEIGHT_HASHTAG,
                )
                .limit(1)
            )
            check_result = await self.repo.session.execute(check_stmt)
            has_enough_weight = check_result.first() is not None

        # Шаг 2: Если весов пока нет — просто выдаём посты по дате
        if not has_enough_weight:
            stmt = (
                select(
                    self.repo.model,
                    exists()
                    .where((Likes.post_id == Posts.id) & (Likes.user_id == user_id))
                    .label("is_liked_by_me"),
                )
                .order_by(Posts.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
            result = await self.repo.session.execute(stmt)
            count_stmt = select(func.count()).select_from(self.repo.model)
            total_count = await self.repo.session.scalar(count_stmt) or 0
            return FilterResult(
                result=[(post, is_liked) for post, is_liked in result.all()],
                pages_count=ceil(total_count / limit),
            )

        # Шаг 3: Весов достаточно — включаем персонализацию
        # сортируем по created_at → author_weight → hashtag_weight_sum
        # не выводим посты, если вес автора < MIN_WEIGHT_AUTHOR и сумма веса хештегов < MIN_SUM_WEIGHT_HASHTAGS
        base_weighted_stmt = (
            select(Posts.id)
            .outerjoin(
                AuthorWeight,
                and_(
                    AuthorWeight.user_id == user_id,
                    AuthorWeight.author_id == Posts.user_id,
                ),
            )
            .outerjoin(PostHashtag, Posts.id == PostHashtag.post_id)
            .outerjoin(
                HashtagWeight,
                and_(
                    HashtagWeight.user_id == user_id,
                    HashtagWeight.hashtag_id == PostHashtag.hashtag_id,
                ),
            )
            .group_by(Posts.id, AuthorWeight.weight)
            .having(
                or_(
                    func.coalesce(AuthorWeight.weight, 0) >= MIN_WEIGHT_AUTHOR,
                    func.coalesce(func.sum(HashtagWeight.weight), 0)
                    >= MIN_SUM_WEIGHT_HASHTAGS,
                )
            )
        )

        base_weighted_subquery = base_weighted_stmt.subquery()
        count_stmt = select(func.count()).select_from(base_weighted_subquery)
        total_count = await self.repo.session.scalar(count_stmt) or 0
        pages_count = ceil(total_count / limit)

        weighted_stmt = (
            select(
                self.repo.model,
                exists()
                .where((Likes.post_id == Posts.id) & (Likes.user_id == user_id))
                .label("is_liked_by_me"),
                func.coalesce(AuthorWeight.weight, 0).label("author_weight"),
                func.coalesce(func.sum(HashtagWeight.weight), 0).label(
                    "hashtag_weight_sum"
                ),
            )
            .outerjoin(
                AuthorWeight,
                and_(
                    AuthorWeight.user_id == user_id,
                    AuthorWeight.author_id == Posts.user_id,
                ),
            )
            .outerjoin(PostHashtag, Posts.id == PostHashtag.post_id)
            .outerjoin(
                HashtagWeight,
                and_(
                    HashtagWeight.user_id == user_id,
                    HashtagWeight.hashtag_id == PostHashtag.hashtag_id,
                ),
            )
            .group_by(Posts.id, AuthorWeight.weight)
            .having(
                or_(
                    func.coalesce(AuthorWeight.weight, 0) >= MIN_WEIGHT_AUTHOR,
                    func.coalesce(func.sum(HashtagWeight.weight), 0)
                    >= MIN_SUM_WEIGHT_HASHTAGS,
                )
            )
            .order_by(
                Posts.created_at.desc(),
                func.coalesce(AuthorWeight.weight, 0).desc(),
                func.coalesce(func.sum(HashtagWeight.weight), 0).desc(),
            )
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.repo.session.execute(weighted_stmt)

        return FilterResult(
            result=[(post, is_liked) for post, is_liked, *_ in result.all()],
            pages_count=pages_count,
        )
