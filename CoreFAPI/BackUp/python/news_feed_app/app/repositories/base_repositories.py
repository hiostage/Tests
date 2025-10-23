from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from database.models.base import Base
from fastapi import HTTPException, status
from sqlalchemy import ColumnElement, and_, exists, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T", bound=Base)


class BaseCRUD(Generic[T]):
    """
    Базовый класс для выполнения CRUD-операций (Create, Read, Update, Delete) с использованием SQLAlchemy.

    Этот класс предоставляет универсальные методы для работы с моделями SQLAlchemy.
    Наследуйте этот класс и укажите конкретную модель в атрибуте `_model`.
    """

    type_model: Type[T]

    def __init__(self, session: "AsyncSession"):
        """
        Инициализирует экземпляр класса BaseCRUD.

        :param session: Асинхронная сессия SQLAlchemy.
        """
        self.__session = session
        self.__model: Type[T] = self.type_model
        object.__setattr__(self, "type_model", property(lambda obj: obj.__model))

    def create(self, data: Dict[str, Any]) -> T:
        """
        Создает новый объект модели и добавляет его в сессию.

        :param data: Словарь с данными для создания объекта.

        :return: Созданный объект модели.
        """
        model_obj = self.model(**data)
        self.session.add(model_obj)
        return model_obj

    @staticmethod
    def update(model_obj: T, data: Dict[str, Any]) -> Optional[T]:
        """
        Обновляет атрибуты объекта модели.

        :param model_obj: Объект модели, который нужно обновить.
        :param data: Словарь с данными для обновления.

        :return: Обновленный объект модели.
        """
        for key, value in data.items():
            setattr(model_obj, key, value)
        return model_obj

    async def get(self, model_obj_id: int) -> Optional[T]:
        """
        Получает объект модели по его ID.

        :param model_obj_id: ID объекта.

        :return: Объект модели или None, если объект не найден.
        """
        return await self.session.get(self.model, model_obj_id)

    async def delete(self, model_obj: T) -> None:
        """
        Удаляет объект модели из сессии.

        :param model_obj: Объект модели, который нужно удалить.

        :return: None
        """
        await self.session.delete(model_obj)

    async def commit(self) -> None:
        """
        Фиксирует изменения в базе данных.

        Этот метод выполняет `commit` для текущей сессии, сохраняя все изменения,
        которые были сделаны в рамках текущей транзакции.

        :return: None
        """
        await self.session.commit()

    @property
    def session(self) -> "AsyncSession":
        """
        Возвращает текущую асинхронную сессию.

        :return: Асинхронная сессия (AsyncSession), связанная с этим объектом.
        """
        return self.__session

    @property
    def model(self) -> Type[T]:
        """
        Возвращает класс модели, связанной с этим репозиторием.

        :return: Класс модели (Type[T]), с которой работает репозиторий.
        """
        return self.__model


class BaseRepository(BaseCRUD[T]):
    """
    Базовый репозиторий для выполнения операций с моделями SQLAlchemy.

    Наследует функциональность класса BaseCRUD и добавляет дополнительные методы.
    """

    async def get_all(self) -> Sequence[T]:
        """
        Получает все объекты модели из базы данных.

        :return: Список всех объектов модели.
        """
        query = await self.session.execute(select(self.model))
        return query.scalars().all()

    async def get_in(self, ids: Sequence[int]) -> Sequence[T]:
        """
        Получает объекты модели по списку их ID.

        :param ids: Список ID объектов.
        :return: Список объектов модели, соответствующих указанным ID.
        """
        if not ids:
            return []
        query = await self.session.execute(
            select(self.model).where(self.model.id.in_(ids))  # type: ignore
        )
        return query.scalars().all()

    async def get_filter_by(self, **kwargs: Any) -> Sequence[T]:
        """
        Получает все объекты модели, соответствующие заданным критериям фильтрации.

        Этот метод использует `filter_by` для фильтрации объектов модели по указанным
        именованным аргументам. Все условия объединяются с помощью оператора `AND`.

        :param kwargs: Именованные аргументы, где ключ — это имя колонки,
                      а значение — условие фильтрации.
        :return: Список объектов модели, соответствующих критериям фильтрации.
        """
        query = await self.session.execute(select(self.model).filter_by(**kwargs))
        return query.scalars().all()

    async def get_filter(self, *conditions: Any) -> Sequence[T]:
        """
        Получает все объекты модели, соответствующие заданным критериям фильтрации.

        Этот метод использует `filter` для фильтрации объектов модели по указанным
        условиям. Условия могут быть сложными и включать SQL-выражения, такие, как
        `and_`, `or_`, сравнения и функции.

        :param conditions: Условия фильтрации в виде SQL-выражений.
        :return: Список объектов модели, соответствующих критериям фильтрации.
        """
        query = await self.session.execute(select(self.model).filter(*conditions))
        return query.scalars().all()

    def bulk_create(self, data_seq: Sequence[Dict[str, Any]]) -> List[T]:
        """
        Массово создает экземпляры модели и добавляет их в сессию.

        Ожидаемое поведение:
        - На основе данных из `data_seq` создаются экземпляры модели.
        - Все созданные экземпляры добавляются в текущую сессию.
        - Возвращается список созданных экземпляров.

        :param data_seq: Последовательность словарей, где каждый словарь содержит данные
                         для создания экземпляра модели.
        :return: Список созданных экземпляров модели.
        """
        list_obj = [self.model(**data) for data in data_seq]
        self.session.add_all(list_obj)
        return list_obj

    async def bulk_delete(self, model_objs: Sequence[T]) -> None:
        """
        Удаляет несколько объектов модели из сессии.

        :param model_objs: Список объектов модели, которые нужно удалить.

        :return: None
        """
        for model_obj in model_objs:
            await self.session.delete(model_obj)

    async def get_or_404(self, model_obj_id: int) -> T:
        """
        Получает объект модели по его ID или вызывает HTTPException 404, если объект не найден.

        :param model_obj_id: ID объекта для поиска в базе данных.
        :return: Найденный объект модели.
        :raises HTTPException: Если объект не найден (status_code=404).
        """
        obj = await self.session.get(self.model, model_obj_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} с ID {model_obj_id} не найден.",
            )
        return obj

    async def one_or_none(self, **kwargs: Any) -> Optional[T]:
        """
        Выполняет запрос к базе данных и возвращает один объект модели или None, если объект не найден.

        :param kwargs: Ключевые аргументы для фильтрации объектов по атрибутам модели.
        :return: Объект модели, если найден ровно один объект, удовлетворяющий условиям фильтрации; иначе None.
        """
        query = await self.session.execute(select(self.model).filter_by(**kwargs))
        return query.scalars().one_or_none()

    async def exists_by_id(self, model_obj_id: int) -> bool:
        """
        Проверяет существование объекта в базе данных по его ID.

        :param model_obj_id: ID объекта для проверки
        :return: True, если объект существует, False иначе
        """
        stmt = select(exists().where(self.model.id == model_obj_id))  # type: ignore
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_by_data(
        self, *args: ColumnElement[bool], **kwargs: Dict[str, Any]
    ) -> bool:
        """
        Проверяет существование записи используя SQL условия или фильтры по полям модели.

        :param args: SQLAlchemy BinaryExpression условия для фильтрации.
                    Пример: [User.id == 1, User.name == "test"]
        :param kwargs: Пары ключ-значение для фильтрации по полям модели.
                    Пример: user_id=uuid1, author_id=uuid2
        :return: True если запись существует, False если нет
        :raises ValueError: Если переданы оба типа параметров (args + kwargs)
                          или не переданы вообще
        :raises AttributeError: Если в kwargs передано несуществующее поле модели
        """
        if (args and kwargs) or (not args and not kwargs):
            raise ValueError("Используйте либо условия, либо фильтры по ключам")

        if args:  # SQLAlchemy условия
            conditions = args
        else:  # Фильтры по полям модели
            conditions = tuple(getattr(self.model, k) == v for k, v in kwargs.items())

        stmt = select(exists().where(and_(*conditions)))
        return bool(await self.session.scalar(stmt))

    async def exists_or_404(self, model_obj_id: int) -> bool:
        """
        Проверяет существование объекта в базе данных по его ID и возвращает True, если объект существует.
        Если объект не найден, возвращает ошибку 404.

        :param model_obj_id: ID объекта для проверки
        :return: True, если объект существует
        :raises HTTPException: Если объект не найден (404 Not Found)
        """
        obj_exists = await self.exists_by_id(model_obj_id)
        if not obj_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} с ID {model_obj_id} не найден.",
            )
        return True

    async def exists_or_404_by_data(
        self, *args: ColumnElement[bool], **kwargs: Dict[str, Any]
    ) -> bool:
        """
        Проверяет существование записи по заданным условиям или фильтрам.
        Если запись не найдена, возбуждает HTTPException с кодом 404.

        :param args: SQLAlchemy BinaryExpression условия для фильтрации.
                     Пример: [User.id == 1, User.name == "test"]
        :param kwargs: Пары ключ-значение для фильтрации по полям модели.
                       Пример: user_id=uuid1, author_id=uuid2
        :return: True, если запись существует.
        :raises HTTPException: 404, если запись не найдена.
        :raises ValueError: Если переданы одновременно args и kwargs или ни одного из них.
        :raises AttributeError: Если kwargs содержит несуществующее поле модели.
        """

        obj_exists = await self.exists_by_data(*args, **kwargs)
        if not obj_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} не найден.",
            )
        return True
