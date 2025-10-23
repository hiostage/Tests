from typing import Generic, TypeVar

T = TypeVar("T")


class BaseService(Generic[T]):
    """
    Базовый сервис для работы с репозиторием.
    """

    def __init__(self, repo: T):
        """
        Инициализирует сервис с указанным репозиторием.

        :param repo: Репозиторий, с которым будет работать сервис.
        """
        self.__repo = repo

    @property
    def repo(self) -> T:
        """
        Возвращает репозиторий, связанный с этим сервисом.

        :return: Репозиторий, с которым работает сервис.
        """
        return self.__repo
