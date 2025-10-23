from typing import Annotated

from dependencies.db import DbSessionDep  # noqa: TC002
from fastapi import Depends
from repositories.attachments import AttachmentsRepository
from repositories.comments import CommentsRepository
from repositories.likes import LikesRepository
from repositories.posts import PostsRepository
from repositories.subscriptions import SubscriptionsRepository


def get_posts_repository(session: DbSessionDep) -> PostsRepository:
    """
    Создает и возвращает репозиторий для работы с постами.

    :param session: DbSessionDep.
    :return: Экземпляр PostsRepository.
    """
    return PostsRepository(session=session)


PostsRepoDep = Annotated[PostsRepository, Depends(get_posts_repository)]


def get_attachments_repository(session: DbSessionDep) -> AttachmentsRepository:
    """
    Создает и возвращает репозиторий для работы с вложениями.

    :param session: DbSessionDep.
    :return: AttachmentsRepository.
    """
    return AttachmentsRepository(session=session)


AttachmentsRepoDep = Annotated[
    AttachmentsRepository, Depends(get_attachments_repository)
]


def get_likes_repository(session: DbSessionDep) -> LikesRepository:
    """
    Создает и возвращает репозиторий для работы с лайками.

    :param session: DbSessionDep.
    :return: LikesRepository.
    """
    return LikesRepository(session=session)


LikesRepoDep = Annotated[LikesRepository, Depends(get_likes_repository)]


def get_comments_repository(session: DbSessionDep) -> CommentsRepository:
    """
    Создает и возвращает репозиторий для работы с комментариями.

    :param session: DbSessionDep.
    :return: CommentsRepository.
    """
    return CommentsRepository(session=session)


CommentsRepoDep = Annotated[CommentsRepository, Depends(get_comments_repository)]


def get_subscriptions_repository(session: DbSessionDep) -> SubscriptionsRepository:
    """
    Фабричная функция для получения экземпляра репозитория подписок.

    :param session: Сессия базы данных.
    :return: Экземпляр SubscriptionsRepository, связанный с переданной сессией.
    """
    return SubscriptionsRepository(session=session)


SubscriptionsRepoDep = Annotated[
    SubscriptionsRepository, Depends(get_subscriptions_repository)
]
