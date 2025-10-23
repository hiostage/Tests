import logging
import sys, os
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """Форматирование логов в JSON для машинного анализа"""
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": "interest_groups",
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging(
    log_dir: str = "logs",
    log_file: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Настройка комплексного логирования с:
    - Ротацией логов
    - JSON-форматированием для production
    - Консольным выводом для разработки
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("interest_groups")
    logger.setLevel(log_level)
    
    # Удаляем все существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Форматтеры
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    back_count = 3
    # File Handler (Production)
    file_handler = RotatingFileHandler(
        filename=Path(log_dir) / log_file,
        maxBytes=max_bytes,
        backupCount=back_count,
        encoding="utf-8"
    )
    file_handler.setFormatter(json_formatter)
    
    # Console Handler (Development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    
    # В development добавляем консольный вывод
    if os.getenv("ENV", "production").lower() == "development":
        logger.addHandler(console_handler)
    
    # Настройка логов для сторонних библиотек
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """Получение настроенного логгера с указанием имени"""
    return logging.getLogger(f"interest_groups.{name}" if name else "interest_groups")

# Инициализация
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO")
)