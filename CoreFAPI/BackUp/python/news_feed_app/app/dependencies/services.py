from typing import Annotated

from dependencies.repositories import (  # noqa: TC002
    AttachmentsRepoDep,
    CommentsRepoDep,
    LikesRepoDep,
    PostsRepoDep,
    SubscriptionsRepoDep,
)
from fastapi import Depends
from services.attachments import AttachmentsService
from services.comments import CommentsService
from services.likes import LikesService
from services.posts import PostsService
from services.subscriptions import SubscriptionsService


def get_posts_service(
    posts_repository: PostsRepoDep,
) -> PostsService:
    """
    Создает сервис для работы с постами.

    :param posts_repository: Репозиторий постов
    :return: PostsService
    """
    return PostsService(posts_repository)


PostsServiceDep = Annotated[PostsService, Depends(get_posts_service)]


def get_attachments_service(
    attachments_repository: AttachmentsRepoDep,
) -> AttachmentsService:
    """
    Создает сервис для работы с вложениями.

    :param attachments_repository: Репозиторий вложений
    :return: AttachmentsService
    """
    return AttachmentsService(attachments_repository)


AttachmentsServiceDep = Annotated[AttachmentsService, Depends(get_attachments_service)]


def get_likes_service(likes_repository: LikesRepoDep) -> LikesService:
    """
    Создает сервис для работы с лайками.

    :param likes_repository: Репозиторий лайков
    :return: LikesService
    """
    return LikesService(likes_repository)


LikesServiceDep = Annotated[LikesService, Depends(get_likes_service)]


def get_comments_service(comments_repository: CommentsRepoDep) -> CommentsService:
    """
    Создает сервис для работы с комментариями.

    :param comments_repository: Репозиторий комментариев
    :return: CommentsService
    """
    return CommentsService(comments_repository)


CommentsServiceDep = Annotated[CommentsService, Depends(get_comments_service)]


def get_subscriptions_service(
    subscriptions_repository: SubscriptionsRepoDep,
) -> SubscriptionsService:
    """
    Фабричная функция для получения экземпляра сервиса подписок.

    :param subscriptions_repository: Репозиторий подписок.
    :return: Экземпляр SubscriptionsService, использующий указанный репозиторий.
    """
    return SubscriptionsService(subscriptions_repository)


SubscriptionsServiceDep = Annotated[
    SubscriptionsService, Depends(get_subscriptions_service)
]
