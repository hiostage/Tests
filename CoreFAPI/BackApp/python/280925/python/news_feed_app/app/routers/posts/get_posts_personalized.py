from logging import Logger
from typing import Annotated, List

from dependencies.loger import get_loger
from dependencies.services import PostsServiceDep  # noqa: TC002
from fastapi import Depends, Query
from routers.posts.access import PostReadUser  # noqa: TC002
from routers.posts.router import posts_router
from schemas.exception_schema import ErrorSchema
from schemas.posts import OutPosts, PostRead


@posts_router.get(
    "/news/posts/personalized",
    response_model=OutPosts,
    name="Получение персонализированной ленты постов",
    description=(
        "Возвращает список постов (с пагинацией), персонализированный для текущего пользователя "
        "с учётом его интересов (веса авторов и хештегов). "
        "Если у пользователя недостаточно данных для персонализации, "
        "возвращаются все посты (с пагинацией) по дате создания."
    ),
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
    },
)
async def get_posts_personalized(
    log: Annotated[Logger, Depends(get_loger("get_posts_personalized"))],
    posts_service: PostsServiceDep,
    user: PostReadUser,
    page: Annotated[int, Query(..., gt=0)] = 1,
    limit: Annotated[int, Query(..., gt=0, le=100)] = 10,
) -> OutPosts:
    """
    Обрабатывает запрос на получение персонализированной ленты постов для авторизованного пользователя.

    Логика:
    - Проверяет, что у пользователя есть идентификатор (user.id).
    - Логирует начало запроса.
    - Вызывает сервис posts_service для получения персонализированной ленты с учётом интересов пользователя,
      передавая параметры пагинации (limit и page).
    - Логирует успешное получение данных.
    - Формирует список постов с информацией о том, лайкнул ли пользователь каждый из них.
    - Возвращает результат в формате OutPosts, включающем список постов и количество страниц.

    Параметры:
    :param log: Логгер с контекстом запроса.
    :param posts_service: Сервис для работы с постами.
    :param user: Авторизованный пользователь, для которого формируется лента.
    :param page: Номер страницы (начинается с 1).
    :param limit: Количество постов на страницу (максимум 100).

    Возвращает:
    :return: Объект OutPosts с постами и количеством страниц.
    """
    log.info(
        "Пользователь id=%s запрашивает персонализированную ленту новостей.", user.id
    )
    result_personalized = await posts_service.get_personalized_feed(
        user.id, limit, page
    )
    log.info(
        "Персонализированная лента новостей успешно возвращена пользователю с id=%s",
        user.id,
    )
    posts_list: List[PostRead] = []
    for post, liked in result_personalized.result:
        response_post = PostRead.model_validate(post)
        response_post.is_liked_by_me = liked
        posts_list.append(response_post)

    return OutPosts(posts=posts_list, count_pages=result_personalized.pages_count)
