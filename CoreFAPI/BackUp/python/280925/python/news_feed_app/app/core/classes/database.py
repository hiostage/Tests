from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
    )
    from sqlalchemy.orm import Session


class Database:
    """
    Класс работы с БД.
    Инициализирует асинхронный движок SQLAlchemy и фабрику сессий.
    """

    def __init__(self, db_url: str) -> None:
        self.__engine = create_async_engine(db_url)
        self.__async_sessionmaker = async_sessionmaker(
            self.__engine, expire_on_commit=False
        )

    def get_engine(self) -> "AsyncEngine":
        """
        Возвращает объект движка базы данных.

        :return: AsyncEngine.
        """
        return self.__engine

    def get_session_fabric(self) -> async_sessionmaker["AsyncSession"]:
        """
        Свойство, возвращающее фабрику сессий.

        :return: Фабрику сессий.
        """
        return self.__async_sessionmaker


class SyncDatabase:
    """
    Класс для синхронного подключения к базе данных с использованием SQLAlchemy.

    :param db_url: URL подключения к базе данных.
    """

    def __init__(self, db_url: str) -> None:
        self.__engine = create_engine(db_url)
        self.__sessionmaker = sessionmaker(bind=self.__engine)

    def get_sync_engine(self) -> "Engine":
        """
        Возвращает экземпляр синхронного движка SQLAlchemy.

        :return: Engine
        """
        return self.__engine

    def get_sync_session_fabric(self) -> sessionmaker["Session"]:
        """
        Возвращает фабрику сессий для синхронной работы с базой данных.

        :return: sessionmaker[Session]
        """
        return self.__sessionmaker
