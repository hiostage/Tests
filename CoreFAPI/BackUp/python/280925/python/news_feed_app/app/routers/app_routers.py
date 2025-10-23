from typing import TYPE_CHECKING, Sequence

from routers.comments import comments_router
from routers.likes import likes_router
from routers.media import media_router
from routers.posts import posts_router
from routers.subscriptions import subscriptions_router

if TYPE_CHECKING:
    from fastapi import APIRouter

routers: Sequence["APIRouter"] = (
    # Тут будем собирать все роуты приложения
    media_router,  # Роут, для работы с медиа.
    posts_router,  # Роут, для работы с постом.
    likes_router,  # Роут, для работы с лайками.
    comments_router,  # Роут, для работы с комментариями.
    subscriptions_router,  # Роут, для работы с подписками.
)
