from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING, Any, Generic, List, Sequence, Set, Tuple, TypeVar

from database.models import Posts, Subscriptions
from database.models.hashtags import Hashtags, PostHashtag
from sqlalchemy import func

if TYPE_CHECKING:

    from schemas.posts import FilterPosts
    from schemas.users import User

T = TypeVar("T")
S = TypeVar("S", bound=Any)


@dataclass
class ObjectListsInspect(Generic[T]):
    """
    Контейнер для результатов сравнения двух списков объектов.

    :ivar new_obj: Объекты, присутствующие только в новом списке
    :ivar both_obj: Объекты, присутствующие в обоих списках
    :ivar deleted_obj: Объекты, отсутствующие в новом списке
    """

    new_obj: Sequence[T]
    both_obj: Sequence[T]
    deleted_obj: Sequence[T]


def inspect_object_lists(
    old_obj_list: Sequence[T], new_obj_list: Sequence[T]
) -> ObjectListsInspect[T]:
    """
    Анализирует различия между двумя списками объектов.

    :param old_obj_list: Исходный список объектов для сравнения
    :param new_obj_list: Новый список объектов для сравнения
    :return: Объект ObjectListsInspect с тремя категориями:
        - new_obj: Объекты, добавленные в новый список
        - both_obj: Объекты, присутствующие в обоих списках
        - deleted_obj: Объекты, удалённые из нового списка

    :Важное примечание:
    Объекты должны быть хешируемыми. Для сложных объектов
    убедитесь, что определены __hash__ и __eq__ методы.
    """
    existing_obj_set: Set[T] = set(old_obj_list)
    new_obj_set: Set[T] = set(new_obj_list)

    return ObjectListsInspect(
        new_obj=list(new_obj_set - existing_obj_set),
        both_obj=list(new_obj_set & existing_obj_set),
        deleted_obj=list(existing_obj_set - new_obj_set),
    )


def user_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Добавляет фильтр по user_id к списку фильтров, если он задан.

    Проверяет, указан ли в объекте filter_posts параметр user_id. Если да,
    добавляет условие фильтрации по user_id в filter_list.

    :param filter_list: Список условий фильтрации, к которому добавляется новое условие.
    :param filter_posts: Объект фильтрации с параметрами для фильтрации постов.
    :param stmt: Исходный запрос (SQLAlchemy Select), который фильтруется.
    :param current_user: Текущий пользователь.
    :return: Исходный запрос без изменений (фильтры добавляются в filter_list).
    """
    if filter_posts.user_id:
        filter_list.append(Posts.user_id == filter_posts.user_id)
    return stmt


def date_from_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Добавляет фильтр по дате создания поста, начиная с указанной даты.

    Если в объекте filter_posts задан параметр `date_from`, добавляет условие,
    которое ограничивает выборку постов датой создания не ранее `date_from`.

    :param filter_list: Список условий фильтрации, к которому добавляется новое условие.
    :param filter_posts: Объект фильтрации с параметрами для фильтрации постов.
    :param stmt: Исходный запрос (SQLAlchemy Select), который фильтруется.
    :param current_user: Текущий пользователь.
    :return: Исходный запрос без изменений (фильтры добавляются в filter_list).
    """
    if filter_posts.date_from:
        start_of_day = datetime.combine(filter_posts.date_from, time.min)
        filter_list.append(Posts.created_at >= start_of_day)
    return stmt


def date_to_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Добавляет фильтр по дате создания поста, ограничивающий выборку постов датой не позже указанной.

    Если в объекте filter_posts задан параметр `date_to`, добавляет условие,
    которое ограничивает выборку постов датой создания не позже `date_to`.

    :param filter_list: Список условий фильтрации, к которому добавляется новое условие.
    :param filter_posts: Объект фильтрации с параметрами для фильтрации постов.
    :param stmt: Исходный запрос (SQLAlchemy Select), который фильтруется.
    :param current_user: Текущий пользователь.
    :return: Исходный запрос без изменений (фильтры добавляются в filter_list).
    """
    if filter_posts.date_to:
        end_of_day = datetime.combine(
            filter_posts.date_to + timedelta(days=1), time.min
        )
        filter_list.append(Posts.created_at < end_of_day)
    return stmt


def search_title_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Добавляет фильтр по поиску подстроки в заголовке поста.

    Если в объекте filter_posts задан параметр `search_title`, добавляет условие,
    которое ищет посты, у которых заголовок содержит указанную подстроку (без учёта регистра).

    :param filter_list: Список условий фильтрации, к которому добавляется новое условие.
    :param filter_posts: Объект фильтрации с параметрами для фильтрации постов.
    :param stmt: Исходный запрос (SQLAlchemy Select), который фильтруется.
    :param current_user: Текущий пользователь.
    :return: Исходный запрос без изменений (фильтры добавляются в filter_list).
    """
    if filter_posts.search_title:
        filter_list.append(Posts.title.ilike(f"%{filter_posts.search_title}%"))
    return stmt


def search_content_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Добавляет фильтр по поиску подстроки в содержимом поста.

    Если в объекте filter_posts задан параметр `search_content`, добавляет условие,
    которое ищет посты, у которых содержимое содержит указанную подстроку (без учёта регистра).

    :param filter_list: Список условий фильтрации, к которому добавляется новое условие.
    :param filter_posts: Объект фильтрации с параметрами для фильтрации постов.
    :param stmt: Исходный запрос (SQLAlchemy Select), который фильтруется.
    :param current_user: Текущий пользователь.
    :return: Исходный запрос без изменений (фильтры добавляются в filter_list).
    """
    if filter_posts.search_content:
        filter_list.append(Posts.content.ilike(f"%{filter_posts.search_content}%"))
    return stmt


def hashtags_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Добавляет фильтрацию постов по заданным хештегам.

    Если в объекте filter_posts задан список хештегов `hashtags`, функция модифицирует
    запрос `stmt`, добавляя JOIN с таблицами хештегов и условия, чтобы выбрать только
    те посты, которые содержат все указанные хештеги.

    Логика фильтрации:
    - Выполняется JOIN с таблицами постов и хештегов.
    - Фильтрация по именам хештегов из списка.
    - Группировка по ID поста.
    - Ограничение выборки постов, у которых количество уникальных совпадающих хештегов
      не меньше длины списка фильтра (т.е. пост содержит все указанные хештеги).

    :param filter_list: Список условий фильтрации (не используется в данной функции).
    :param filter_posts: Объект фильтрации с параметрами для фильтрации постов.
    :param stmt: Исходный запрос (например, SQLAlchemy Select), который модифицируется.
    :param current_user: Текущий пользователь.
    :return: Модифицированный запрос с применённым фильтром по хештегам.
    """
    if filter_posts.hashtags:
        stmt = (
            stmt.join(Posts.post_hashtags)
            .join(PostHashtag.hashtag)
            .where(Hashtags.name.in_(filter_posts.hashtags))
            .group_by(Posts.id)
            .having(
                func.count(func.distinct(Hashtags.name)) >= len(filter_posts.hashtags)
            )
        )
    return stmt


def subscriptions_posts_filter(
    filter_list: List[Any], filter_posts: "FilterPosts", stmt: S, current_user: "User"
) -> S:
    """
    Применяет фильтр подписок к запросу постов.

    Если в фильтре установлен флаг `subscriptions=True` и пользователь аутентифицирован,
    добавляет в запрос JOIN с таблицей подписок, чтобы отфильтровать посты только от авторов,
    на которых подписан текущий пользователь.

    :param filter_list: Список дополнительных фильтров (не используется в данном коде, но может быть расширен).
    :param filter_posts: Объект фильтра с параметрами запроса.
    :param stmt: Исходный SQLAlchemy запрос (select).
    :param current_user: Текущий аутентифицированный пользователь.
    :return: Модифицированный SQLAlchemy запрос с применённым фильтром подписок.
    """
    if filter_posts.subscriptions and current_user.id:
        stmt = stmt.join(Subscriptions, Subscriptions.author_id == Posts.user_id).where(
            Subscriptions.user_id == current_user.id
        )
    return stmt


M = TypeVar("M")


@dataclass
class FilterResult(Generic[M]):
    """
    Класс для хранения результата фильтрации с пагинацией.

    :ivar result: Последовательность кортежей, где каждый кортеж содержит объект типа M и булево значение (наличие лайка).
    :ivar pages_count: Общее количество страниц с результатами.
    """

    result: Sequence[Tuple[M, bool]]
    pages_count: int


@dataclass
class SubscriptionsResult:
    """
    Класс для результата запроса подписок с пагинацией.

    :ivar subscriptions: Последовательность объектов подписок.
    :ivar pages_count: Общее количество страниц с подписками.
    """

    subscriptions: Sequence[Subscriptions]
    pages_count: int
