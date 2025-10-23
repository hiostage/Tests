from abc import ABC
from datetime import date, datetime  # noqa: TC003
from typing import List, Optional, Self
from uuid import UUID  # noqa: TC003

from database.models.hashtags import HASHTAG_PATTERN
from database.models.posts import MAX_CONTENT_LENGTH, MAX_TITLE_LENGTH
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from schemas.attachments import OutAttachmentSchema  # noqa: TC002
from schemas.base import BaseSchema
from schemas.hashtags import OutHashtags  # noqa: TC002

MAX_ATTACHMENTS = 30
MAX_HASHTAGS = 30


class ValidatePostHashtags(ABC):
    """
    Абстрактный класс для валидации хештегов.
    """

    hashtag_names: List[str] | None

    @field_validator("hashtag_names", mode="before")
    @classmethod
    def validate_hashtags(cls, hashtags: List[str] | None) -> List[str] | None:
        """
        Валидирует и нормализует список хэштегов.

        :param hashtags: Список сырых хэштегов из входных данных
        :return: Очищенный список валидных хэштегов в нижнем регистре
        :raises ValueError: Если какой-либо хэштег не проходит валидацию

        Особенности обработки:
        - Удаляет пробелы в начале/конце
        - Приводит к нижнему регистру
        - Добавляет # если отсутствует
        - Проверяет соответствие паттерну HASHTAG_PATTERN

        Примеры преобразований:
        - "  Python  " -> "#python"
        - "codereview" -> "#codereview"
        - "#AlreadyValid" -> "#alreadyvalid"

        Недопустимые примеры:
        - "##doublehash" (повтор #)
        - "#with space" (пробелы в хэштеге)
        - "#спецсимволы!" (недопустимые символы)
        """
        if hashtags is None:
            return hashtags
        cleaned = []
        for tag in hashtags:
            tag = tag.lower().strip()
            if not tag:
                continue

            if not tag.startswith("#"):
                tag = f"#{tag}"

            if not HASHTAG_PATTERN.fullmatch(tag):
                raise ValueError(
                    f"Хэштег '{tag}' невалиден. Должен соответствовать шаблону {HASHTAG_PATTERN.pattern}"
                )

            cleaned.append(tag)

        return cleaned


class PostCreate(BaseModel, ValidatePostHashtags):
    """
    Модель для создания нового поста.

    :ivar title: Заголовок поста
    :ivar content: Содержание поста
    :ivar attachments_ids: Список ID вложений
    :ivar hashtag_names: Список названий хэштегов (['#хэштег', ...])
    """

    title: str = Field(max_length=MAX_TITLE_LENGTH)
    content: str = Field(max_length=MAX_CONTENT_LENGTH)
    attachments_ids: List[int] = Field(
        default_factory=list, max_length=MAX_ATTACHMENTS, examples=[[1, 2]]
    )
    hashtag_names: List[str] = Field(
        default_factory=list,
        max_length=MAX_HASHTAGS,
        examples=[["#новости", "#технологии"]],
    )


class OriginalPostRead(BaseModel):
    """
    Схема для чтения данных оригинального поста для репоста.

    :ivar id: Уникальный идентификатор поста
    :ivar title: Заголовок поста
    :ivar content: Содержимое поста
    :ivar user_id: UUID автора поста
    :ivar created_at: Дата создания записи
    :ivar updated_at: Дата последнего обновления
    :ivar attachments: Список вложений (OutAttachmentSchema)
    :ivar hashtags: Исходные хэштеги (исключены из сериализации)
    :ivar hashtag_names: Список имён хэштегов (вычисляемое поле)
    """

    id: int
    title: str
    content: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    attachments: List[OutAttachmentSchema]
    hashtags: List[OutHashtags] = Field(exclude=True)

    @computed_field(
        description="Список имён хэштегов (начинаются с '#')",
        examples=[["#технологии", "#новости"]],
    )
    def hashtag_names(self) -> List[str]:
        """
        Список имён хэштегов, связанных с текущим объектом.

        :return: List[str] — имена хэштегов
        """
        return [hashtag.name for hashtag in self.hashtags]

    model_config = ConfigDict(from_attributes=True)


class PostRead(BaseModel):
    """
    Схема для чтения полных данных поста с метриками активности.

    :ivar id: Уникальный идентификатор поста
    :ivar title: Заголовок поста
    :ivar content: Содержимое поста
    :ivar user_id: UUID автора поста
    :ivar created_at: Дата создания записи
    :ivar updated_at: Дата последнего обновления
    :ivar attachments: Список вложений (OutAttachmentSchema)
    :ivar is_liked_by_me: Флаг лайка текущего пользователя
    :ivar likes_count: Общее количество лайков
    :ivar comments_count: Количество комментариев
    :ivar reposts_count: Количество репостов
    :ivar original_post: Данные оригинального поста (для репостов)
    :ivar hashtags: Исходные хэштеги (исключены из сериализации)
    :ivar hashtag_names: Список имён хэштегов (вычисляемое поле)
    """

    id: int
    title: str | None
    content: str | None
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    attachments: List[OutAttachmentSchema]
    is_liked_by_me: bool = Field(default=False)
    likes_count: int
    comments_count: int
    reposts_count: int
    original_post: OriginalPostRead | None

    hashtags: List[OutHashtags] = Field(exclude=True)

    @computed_field(
        description="Список имён хэштегов (начинаются с '#')",
        examples=[["#технологии", "#новости"]],
    )
    def hashtag_names(self) -> List[str]:
        """
        Список имён хэштегов, связанных с текущим объектом.

        :return: List[str] — имена хэштегов
        """
        return [hashtag.name for hashtag in self.hashtags]

    model_config = ConfigDict(from_attributes=True)


class ShortPostRead(BaseModel):
    """
    Краткая модель для чтения поста.

    :ivar id: ID поста
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


class PostUpdate(BaseModel, ValidatePostHashtags):
    """
    Модель для обновления существующего поста.

    :ivar title: Новый заголовок (опционально)
    :ivar content: Новое содержание (опционально)
    :ivar attachments_ids: Список ID вложений (опционально)
    :ivar hashtag_names: Список хештегов (опционально)
    """

    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    content: str | None = Field(default=None, max_length=MAX_CONTENT_LENGTH)
    attachments_ids: List[int] | None = Field(
        default=None, max_length=MAX_ATTACHMENTS, examples=[[1, 2]]
    )
    hashtag_names: List[str] | None = Field(
        default=None,
        max_length=MAX_HASHTAGS,
        examples=[["#новости", "#технологии"]],
    )


class ShortOutPost(BaseSchema):
    """
    Краткая схема вывода поста.

    :ivar result: Результат операции
    :ivar post: Краткая информация о посте
    """

    post: ShortPostRead


class OutPost(BaseSchema):
    """
    Полная схема вывода поста.

    :ivar result: Результат операции
    :ivar post: Детальная информация о посте
    """

    post: PostRead


class RePostCreate(PostUpdate):
    """
    Модель создания репостов

    :ivar title: Новый заголовок (опционально)
    :ivar content: Новое содержание (опционально)
    :ivar attachments_ids: Список ID вложений (опционально)
    :ivar hashtag_names: Список хештегов (опционально)
    """


class OutPosts(BaseSchema):
    """
    Полная схема вывода постов.

    :ivar result: Результат операции.
    :ivar posts: Список постов.
    :ivar count_pages: Количество всех страниц.
    """

    posts: List[PostRead]
    count_pages: int


class FilterPosts(BaseModel):
    """
    Модель для фильтрации и пагинации постов с валидацией входных данных.

    :ivar user_id: UUID автора поста для фильтрации (опционально).
    :ivar hashtags: Список хештегов для фильтрации (опционально).
    :ivar date_from: Начальная дата диапазона фильтрации (опционально).
    :ivar date_to: Конечная дата диапазона фильтрации (опционально).
    :ivar search_title: Подстрока для поиска в заголовках (опционально).
    :ivar search_content: Подстрока для поиска в содержимом (опционально).
    :ivar page: Номер страницы для пагинации, начиная с 1 (по умолчанию 1).
    :ivar limit: Количество элементов на странице (от 1 до 100, по умолчанию 10).
    :ivar subscriptions: Фильтр по подпискам (если True - только посты из подписок).
    :raises ValueError: При некорректном диапазоне дат (date_from > date_to).
    """

    user_id: Optional[UUID] = Field(default=None)
    hashtags: Optional[List[str]] = Field(default=None)
    date_from: Optional[date] = Field(default=None)
    date_to: Optional[date] = Field(default=None)
    search_title: str | None = Field(default=None)
    search_content: str | None = Field(default=None)
    page: int = Field(default=1, ge=1, description="Номер страницы, начиная с 1")
    limit: int = Field(
        default=10, ge=1, le=100, description="Максимум 100 записей на страницу"
    )
    subscriptions: bool = Field(default=False, description="Только в подписках.")

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        """
        Проверяет корректность диапазона дат.

        Убеждается, что если заданы обе даты `date_from` и `date_to`, то
        `date_from` не позже `date_to`. В противном случае выбрасывает ValueError.

        :raises ValueError: Если `date_from` позже `date_to`.
        :return: Текущий экземпляр FilterPosts.
        """
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("`date_from` не может быть позже `date_to`")
        return self

    @field_validator("search_title", "search_content", mode="before")
    @classmethod
    def strip_search_fields(cls, v: str | None) -> str | None:
        """
        Очищает пробелы в начале и конце поисковых строк.

        Если значение не None, возвращает строку с удалёнными пробелами по краям.
        Иначе возвращает None.

        :param v: Значение поля для очистки.
        :return: Очищенная строка или None.
        """
        return v.strip() if v else v
