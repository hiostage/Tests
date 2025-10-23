import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict

from dotenv import find_dotenv
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppBaseSettings(BaseSettings):
    """
    Базовые настройки приложения.
    Подтягивает все переменные окружения для приложения.

    Важно:
    Атрибуты наследуемого класса от AppBaseSettings должны иметь одинаковое название как у переменных окружения.
    При необходимости переопределите model_config.

    """

    model_config = SettingsConfigDict(
        env_file=find_dotenv(), frozen=True, extra="ignore"
    )


class RabbitSettings(AppBaseSettings):
    """
    Конфигурация параметров подключения к RabbitMQ.

    :ivar RABBITMQ_DEFAULT_USER: Имя пользователя RabbitMQ.
    :ivar RABBITMQ_DEFAULT_PASS: Пароль пользователя RabbitMQ.
    :ivar RABBITMQ_DEFAULT_HOST: Адрес хоста RabbitMQ.
    :ivar RABBITMQ_DEFAULT_PORT: Порт RabbitMQ.
    :ivar MQ_ROUTING_KEY: Основной ключ маршрутизации сообщений.
    :ivar INNER_MQ_ROUTING_KEY: Внутренний ключ маршрутизации сообщений.
    """

    RABBITMQ_DEFAULT_USER: str = ""
    RABBITMQ_DEFAULT_PASS: str = ""
    RABBITMQ_DEFAULT_HOST: str = ""
    RABBITMQ_DEFAULT_PORT: str = ""
    MQ_ROUTING_KEY: str
    INNER_MQ_ROUTING_KEY: str


class MinioEndpoint(AppBaseSettings):
    """
    Класс настроки Minio Endpoint.
    Для получения эндпоинта Minio воспользуйтесь get_endpoint.
    """

    MINIO_HOST: str = ""
    MINIO_PORT: str = ""

    @property
    def get_endpoint(self) -> str:
        """
        Возвращает endpoint.
        """
        return f"{self.MINIO_HOST}:{self.MINIO_PORT}"


class MinIOSettings(AppBaseSettings):
    """
    Класс настроек MinIO.
    Получает атрибуты из переменных окружения.

    """

    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = ""
    MINIO_ENDPOINT: str = ""


class DBSettings(AppBaseSettings):
    """
    Класс настроек DB.
    Получает атрибуты из переменных окружения.
    """

    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: str = ""
    POSTGRES_DB: str = ""

    @property
    def get_postgres_url(self) -> str:
        """
        Возвращает url scheme://username:password@host:port/db_name
        """
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=int(self.POSTGRES_PORT),
            path=self.POSTGRES_DB,
        ).unicode_string()

    @property
    def get_sync_postgres_url(self) -> str:
        """
        Возвращает url scheme://username:password@host:port/db_name
        """
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=int(self.POSTGRES_PORT),
            path=self.POSTGRES_DB,
        ).unicode_string()


class Settings(BaseSettings):
    """
    Общий класс настроек.
    """

    DB_SETTINGS: DBSettings
    JANITOR_SETTINGS: "JanitorSettings"
    DEBUG: bool = Field(default=False)
    LOG_SETTINGS: "LogerSettings"
    MINIO_SETTINGS: MinIOSettings
    BASE_DIR: Path = Field(default=Path(__file__).resolve().parent.parent.parent)
    RABBITMQ_SETTINGS: RabbitSettings

    def makedirs_LOGGING_ROOT(self) -> None:
        """
        Создаёт путь к LOGS.
        """
        for (
            _,
            handler_config,
        ) in self.LOG_SETTINGS.LOGGING_CONFIG.get("handlers", {}).items():
            if "filename" in handler_config:
                log_dir = os.path.dirname(handler_config["filename"])
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)


class LogerSettings(BaseSettings):
    """
    Класс настроек LOGER.
    """

    LOGGING_CONFIG: Dict[str, Any] = Field(
        frozen=True,
    )


class JanitorSettings(BaseSettings):
    """
    Настройки для задачи сборщика мусора.

    :ivar REPEAT_TIME: Интервал между запусками задачи (по умолчанию 1 час)
    :ivar CONSIDER_OLD_FILE: Время, после которого файл считается старым (по умолчанию 1 час)
    :ivar NUMBER_OF_FILES_AT_TIME: Количество файлов, обрабатываемых за раз (по умолчанию 100)
    """

    REPEAT_TIME: timedelta = Field(default=timedelta(hours=1))
    CONSIDER_OLD_FILE: timedelta = Field(default=timedelta(hours=1))
    NUMBER_OF_FILES_AT_TIME: int = Field(default=100, gt=10, lt=1000)

    @field_validator("REPEAT_TIME")
    def validate_repeat_time(cls, value: timedelta) -> timedelta:
        """
        Проверяет, что интервал REPEAT_TIME не меньше 10 минут.

        :param value: Значение интервала
        :return: Значение интервала, если оно валидно
        :raises ValueError: Если интервал меньше 10 минут
        """
        min_duration = timedelta(minutes=10)
        if value < min_duration:
            raise ValueError(
                f"Интервал REPEAT_TIME не может быть меньше {min_duration}. "
                f"Получено: {value}"
            )
        return value

    @field_validator("CONSIDER_OLD_FILE")
    def validate_consider_old_file(cls, value: timedelta) -> timedelta:
        """
        Проверяет, что время CONSIDER_OLD_FILE не меньше 10 минут.

        :param value: Значение времени
        :return: Значение времени, если оно валидно
        :raises ValueError: Если время меньше 10 минут
        """
        min_duration = timedelta(minutes=10)
        if value < min_duration:
            raise ValueError(
                f"CONSIDER_OLD_FILE не может быть меньше {min_duration}. "
                f"Получено: {value}"
            )
        return value
