from logging import Logger
from typing import Annotated, List

from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from fastapi import Depends, Query
from routers.posts.access import PostReadUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.exception_schema import ErrorSchema
from schemas.posts import FilterPosts, OutPosts, PostRead


@posts_router.get(
    "/news/posts/filter",
    response_model=OutPosts,
    name="Получить список новостей (фильтрация).",
    description="Получить список новостей с помощью фильтров (с пагинацией). Фильтры опциональны.",
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
    },
)
async def get_posts_by_filtration(
    log: Annotated[Logger, Depends(get_loger("get_posts_by_filtration"))],
    posts_service: PostsServiceDep,
    user: PostReadUser,
    great_filter: Annotated[FilterPosts, Query(...)],
) -> OutPosts:
    """
    Получает список новостей с применением фильтров и пагинации.

    Выполняет фильтрацию постов по различным критериям (автор, хештеги, даты,
    заголовок, содержимое) с поддержкой пагинации. Для каждого поста дополнительно
    возвращает флаг, указывающий, лайкнул ли его текущий пользователь.

    :param log: Логгер для записи действий.
    :param posts_service: Сервис для работы с постами.
    :param user: Текущий пользователь, для которого определяется наличие лайка.
    :param great_filter: Объект фильтрации с параметрами поиска и пагинации.
    :return: Объект OutPosts со списком постов и количеством страниц.
    """
    log.info("Пользователь id=%s начинает поиск новостей с фильтрами.", user.id)
    result_filter = await posts_service.get_filter_posts_with_liked_current_user(
        user, great_filter
    )
    log.info("Пользователь id=%s. Успешно нашёл посты после фильтрации.", user.id)
    posts_list: List[PostRead] = []
    for post, liked in result_filter.result:
        response_post = PostRead.model_validate(post)
        response_post.is_liked_by_me = liked
        posts_list.append(response_post)

    return OutPosts(posts=posts_list, count_pages=result_filter.pages_count)
