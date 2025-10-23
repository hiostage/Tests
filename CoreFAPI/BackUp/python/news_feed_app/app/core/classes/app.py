import logging.config
from typing import TYPE_CHECKING, Any

from app_utils.rabbitmq_manager import RabbitMQClient
from core.classes.database import Database, SyncDatabase
from fastapi import FastAPI
from minio import Minio

if TYPE_CHECKING:
    from core.classes.settings import Settings


class CustomFastApi(FastAPI):
    """
    Расширенный FastAPI класс.
    """

    def __init__(self, *args: Any, settings: "Settings", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__settings = settings
        self.__db = Database(db_url=settings.DB_SETTINGS.get_postgres_url)
        self.__sync_db = SyncDatabase(db_url=settings.DB_SETTINGS.get_sync_postgres_url)
        self.__settings.makedirs_LOGGING_ROOT()
        logging.config.dictConfig(self.__settings.LOG_SETTINGS.LOGGING_CONFIG)
        self.__minio_client = Minio(
            endpoint=settings.MINIO_SETTINGS.MINIO_ENDPOINT,
            access_key=settings.MINIO_SETTINGS.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SETTINGS.MINIO_SECRET_KEY,
            secure=False,
        )
        self.__rabbit_client = RabbitMQClient(settings)

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Возвращает логер приложения.

        :param name: Имя логера.
        :return: Logger.
        """
        return logging.getLogger(".".join(["my_app", name]))

    def get_settings(self) -> "Settings":
        """
        Возвращает подключенные настройки приложения.

        :return: Settings.
        """
        return self.__settings

    def get_db(self) -> Database:
        """
        Возвращает подключенный к приложению асинхронный инструмент работы с БД.

        :return: Database.
        """
        return self.__db

    def get_sync_db(self) -> SyncDatabase:
        """
        Возвращает подключенный к приложению синхронный инструмент работы с БД.

        :return: SyncDatabase.
        """
        return self.__sync_db

    def get_minio_client(self) -> Minio:
        """
        Возвращает инструмент для работы с Minio.

        :return: Minio.
        """
        return self.__minio_client

    def get_rabbit_client(self) -> RabbitMQClient:
        """
        Возвращает инструмент для работы с RabbitMQ.

        :return: RabbitMQClient.
        """
        return self.__rabbit_client
