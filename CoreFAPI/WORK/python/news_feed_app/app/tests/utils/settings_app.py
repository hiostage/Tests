import copy
from pathlib import Path
from typing import Any, Dict

from settings.app_settings import (
    db_settings,
    logger_settings,
    minio_settings,
    rabbit_settings,
    settings,
)

base_dir = Path(__file__).parent.parent
test_db_settings = db_settings.model_copy(
    update={
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5433",
        "POSTGRES_DB": "test_db",
    }
)
MINIO_BUCKET = "test-images"

min_io_settings = minio_settings.model_copy(
    update={
        "MINIO_ENDPOINT": "localhost:9001",
        "MINIO_ACCESS_KEY": "miniotest",
        "MINIO_SECRET_KEY": "miniotest",
        "MINIO_BUCKET": MINIO_BUCKET,
    }
)
log_conf: Dict[str, Any] = copy.deepcopy(logger_settings.LOGGING_CONFIG)
logs_dir = base_dir / "logs"
logs_dir.mkdir(exist_ok=True)
log_conf["handlers"]["file"]["filename"] = str(logs_dir / "app.log")
log_settings = logger_settings.model_copy(
    update={
        "LOGGING_CONFIG": log_conf,
    }
)
t_rabbit_settings = rabbit_settings.model_copy(
    update={
        "RABBITMQ_DEFAULT_USER": "guest",
        "RABBITMQ_DEFAULT_PASS": "guest",
        "RABBITMQ_DEFAULT_HOST": "localhost",
        "RABBITMQ_DEFAULT_PORT": "5673",
        "MQ_ROUTING_KEY": "test_news_feed",
        "INNER_MQ_ROUTING_KEY": "__test_news_feed",
    }
)
t_settings = settings.model_copy(
    update={
        "BASE_DIR": base_dir,
        "DEBUG": False,
        "DB_SETTINGS": test_db_settings,
        "MINIO_SETTINGS": min_io_settings,
        "LOG_SETTINGS": log_settings,
        "RABBITMQ_SETTINGS": t_rabbit_settings,
    }
)
