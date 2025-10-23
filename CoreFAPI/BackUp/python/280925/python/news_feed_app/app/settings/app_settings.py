from datetime import timedelta
from pathlib import Path

from core.classes.settings import (
    DBSettings,
    JanitorSettings,
    LogerSettings,
    MinioEndpoint,
    MinIOSettings,
    RabbitSettings,
    Settings,
)
from settings.log_settings import get_log_settings

BASE_DIR = Path(__file__).resolve().parent.parent

janitor_settings = JanitorSettings(
    REPEAT_TIME=timedelta(hours=2),
    CONSIDER_OLD_FILE=timedelta(hours=2),
    NUMBER_OF_FILES_AT_TIME=100,
)

minio_settings = MinIOSettings(MINIO_ENDPOINT=MinioEndpoint().get_endpoint)

db_settings = DBSettings()

logger_settings = LogerSettings(LOGGING_CONFIG=get_log_settings(BASE_DIR))

rabbit_settings = RabbitSettings(
    MQ_ROUTING_KEY="news_feed", INNER_MQ_ROUTING_KEY="__news_feed"
)

settings = Settings(
    LOG_SETTINGS=logger_settings,
    DB_SETTINGS=db_settings,
    MINIO_SETTINGS=minio_settings,
    JANITOR_SETTINGS=janitor_settings,
    RABBITMQ_SETTINGS=rabbit_settings,
)
