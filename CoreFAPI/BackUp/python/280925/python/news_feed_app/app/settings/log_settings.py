from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from pathlib import Path


def get_log_settings(base_dir: "Path") -> Dict[str, Any]:
    """
    Возвращает настройки логирования с обработчиками для файла и консоли.

    :param base_dir: Базовая директория для хранения логов
    :return: Словарь с конфигурацией логирования
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s [line: %(lineno)d]",
                "datefmt": "%d.%m.%Y %H:%M:%S",
            },
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": base_dir / "logs" / "app.log",  # Имя файла для логов
                "maxBytes": 1 * 1024 * 1024,  # Максимальный размер файла 1 MB
                "backupCount": 5,  # Количество резервных файлов
                "formatter": "default",
                "level": "DEBUG",  # Уровень логирования для файла
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",  # Уровень логирования для консоли
            },
        },
        "loggers": {
            "my_app": {
                "handlers": ["file", "console"],  # Обработчики для логгера
                "level": "DEBUG",  # Уровень логирования для логгера
                "propagate": False,  # Не передавать логи родительским логгерам
            },
        },
    }
